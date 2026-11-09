<template>
  <LayoutHeader v-if="contact.doc">
    <header
      class="relative flex h-10.5 items-center justify-between gap-2 py-2.5 pl-2"
    >
      <Breadcrumbs :items="breadcrumbs">
        <template #prefix="{ item }">
          <Icon v-if="item.icon" :icon="item.icon" class="mr-2 h-4" />
        </template>
      </Breadcrumbs>
    </header>
  </LayoutHeader>
  <div v-if="contact.doc" class="flex flex-col h-full overflow-hidden">
    <FileUploader
      :validateFile="validateIsImageFile"
      @success="changeContactImage"
    >
      <template #default="{ openFileSelector, error }">
        <div class="flex flex-col items-start justify-start gap-4 p-4">
          <div class="flex gap-4 items-center">
            <div class="group relative h-14.5 w-14.5">
              <Avatar
                size="3xl"
                class="h-14.5 w-14.5"
                :label="contact.doc.full_name"
                :image="contact.doc.image"
              />
              <component
                :is="contact.doc.image ? Dropdown : 'div'"
                v-bind="
                  contact.doc.image
                    ? {
                        options: [
                          {
                            icon: 'lucide-upload',
                            label: contact.doc.image
                              ? __('Change Image')
                              : __('Upload Image'),
                            onClick: openFileSelector,
                          },
                          {
                            icon: 'lucide-trash-2',
                            label: __('Remove Image'),
                            onClick: () => changeContactImage(''),
                          },
                        ],
                      }
                    : { onClick: openFileSelector }
                "
                class="!absolute bottom-0 left-0 right-0"
              >
                <div
                  class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 duration-300 ease-in-out [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover:opacity-100"
                  style="
                    -webkit-clip-path: inset(22px 0 0 0);
                    clip-path: inset(22px 0 0 0);
                  "
                >
                  <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                </div>
              </component>
            </div>
            <div class="flex flex-col gap-2 truncate">
              <div class="truncate text-lg-medium text-ink-gray-9">
                <span v-if="contact.doc.salutation">
                  {{ contact.doc.salutation + '. ' }}
                </span>
                <span>{{ contact.doc.full_name }}</span>
              </div>
              <div class="flex items-center gap-1.5">
                <Button
                  v-if="callEnabled && contact.doc.mobile_no"
                  :label="__('Make a Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  @click="callEnabled && makeCall(contact.doc.mobile_no)"
                />
                <Button
                  v-if="canDelete"
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  icon-left="lucide-trash-2"
                  @click="deleteContact"
                />
                <Avatar
                  v-if="contact.doc.company_name"
                  size="md"
                  :label="contact.doc.company_name"
                  :image="
                    getOrganization(contact.doc.company_name)?.organization_logo
                  "
                />
              </div>
              <ErrorMessage :message="__(error)" />
            </div>
          </div>
        </div>
      </template>
    </FileUploader>
    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-auto flex-col [&_[role='tablist']]:gap-3 [&_[role='tablist']]:px-4 [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow [&>[data-slot=tab-list]]:overflow-x-auto [&_[data-slot=tab-indicator]]:translate-y-0 [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-col [&>[data-slot=tab-panel]]:overflow-auto"
    >
      <template #tab-suffix="{ tab, active }">
        <Badge
          v-if="['transactions', 'trades'].includes(tab.value)"
          :class="[active ? 'bg-surface-gray-10' : 'bg-gray-600']"
          variant="solid"
          theme="gray"
          size="sm"
        >
          {{ tab.count }}
        </Badge>
      </template>
      <template #tab-panel="{ tab }">
        <div v-if="tab.name == 'Details'">
          <div
            v-if="sections.data"
            class="flex flex-1 flex-col justify-between overflow-hidden"
          >
            <SidePanelLayout
              :sections="sections.data"
              doctype="Contact"
              :docname="contact.doc.name"
              @reload="sections.reload"
            />
          </div>
        </div>
        <template
          v-else-if="
            tab.value === 'transactions' && transactionsData.overall_count
          "
        >
          <TransactionPeriodFilter
            v-model:period="transactionPeriod"
            v-model:date-from="transactionDateFrom"
            v-model:date-to="transactionDateTo"
            class="mt-4"
          />
          <TransactionSummaryCards class="mt-3" v-bind="transactionSummary" />
          <TransactionsListView
            v-if="transactionRows.length"
            v-model:page-length="transactionPageLength"
            class="mt-4"
            :rows="transactionRows"
            :columns="transactionColumns"
            :total-count="transactionsData.total_count"
            @load-more="loadTransactions(true)"
          />
          <div v-else class="mt-10 text-center text-p-base text-ink-gray-5">
            {{ __('No transactions in this period.') }}
          </div>
        </template>
        <template
          v-else-if="tab.value === 'trades' && tradesData.overall_count"
        >
          <TransactionPeriodFilter
            v-model:period="tradePeriod"
            v-model:date-from="tradeDateFrom"
            v-model:date-to="tradeDateTo"
            class="mt-4"
          />
          <TradeSummaryCards class="mt-3" :total-trades="tradesData.total_count" />
          <TransactionsListView
            v-if="tradeRows.length"
            v-model:page-length="tradePageLength"
            class="mt-4"
            :rows="tradeRows"
            :columns="tradeColumns"
            :total-count="tradesData.total_count"
            @load-more="loadTrades(true)"
          />
          <div v-else class="mt-10 text-center text-p-base text-ink-gray-5">
            {{ __('No trades in this period.') }}
          </div>
        </template>
        <div
          v-if="
            (tab.value === 'transactions' && !transactionsData.overall_count) ||
            (tab.value === 'trades' && !tradesData.overall_count)
          "
          class="grid flex-1 place-items-center text-2xl-medium text-ink-gray-4"
        >
          <div class="flex flex-col items-center justify-center space-y-3">
            <component :is="tab.iconLeft" class="!h-10 !w-10" />
            <div>{{ __('No {0} found', [__(tab.label.toLowerCase())]) }}</div>
          </div>
        </div>
      </template>
    </Tabs>
  </div>
</template>

<script setup>
import Icon from '@/components/Icon.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideTrendingUp from '~icons/lucide/trending-up'
import TransactionsListView from '@/components/ListViews/TransactionsListView.vue'
import TransactionSummaryCards from '@/components/TransactionSummaryCards.vue'
import { useLinkedTrades } from '@/composables/useLinkedTrades'
import TradeSummaryCards from '@/components/TradeSummaryCards.vue'
import TransactionPeriodFilter from '@/components/TransactionPeriodFilter.vue'
import { validateIsImageFile } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { getView } from '@/utils/view'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { organizationsStore } from '@/stores/organizations.js'
import { callEnabled } from '@/composables/telephony'
import {
  Breadcrumbs,
  Avatar,
  FileUploader,
  Tabs,
  call,
  createResource,
  usePageMeta,
  Dropdown,
  toast,
} from 'frappe-ui'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { useTelemetry } from '@framework/ui/telemetry'
import { ref, reactive, computed, watch, h, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const { brand } = getSettings()
const { $dialog, makeCall } = globalStore()

const { getOrganization } = organizationsStore()
const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const route = useRoute()
const router = useRouter()

const {
  document: contact,
  permissions,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const transformField = useContactFields(contact)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
})

const breadcrumbs = computed(() => {
  let items = [{ label: __('Contacts'), route: { name: 'Contacts' } }]

  if (route.query.view || route.query.viewType) {
    let view = getView(route.query.view, route.query.viewType, 'Contact')
    if (view) {
      items.push({
        label: __(view.label),
        icon: view.icon,
        route: {
          name: 'Contacts',
          params: { viewType: route.query.viewType },
          query: { view: route.query.view },
        },
      })
    }
  }

  items.push({
    label: title.value,
    route: {
      name: 'Contact',
      params: { contactId: props.contactId },
      query: route.query,
    },
  })
  return items
})

const title = computed(() => {
  let t = doctypeMeta.value?.title_field || 'name'
  return contact.doc?.[t] || props.contactId
})

usePageMeta(() => {
  return {
    title: title.value,
    icon: brand.favicon,
  }
})

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact Image Updated'))
    },
  })
}

async function deleteContact() {
  $dialog({
    title: __('Delete Contact'),
    message: __('Are you sure you want to delete this contact?'),
    actions: [
      {
        label: __('Delete'),
        theme: 'red',
        variant: 'solid',
        async onClick({ close }) {
          await call('frappe.client.delete', {
            doctype: 'Contact',
            name: props.contactId,
          })
          close()
          router.push({ name: 'Contacts' })
        },
      },
    ],
  })
}

const {
  data: tradesData,
  rows: tradeRows,
  columns: tradeColumns,
  pageLength: tradePageLength,
  period: tradePeriod,
  dateFrom: tradeDateFrom,
  dateTo: tradeDateTo,
  load: loadTrades,
} = useLinkedTrades(props.contactId)

const activeTab = ref('details')
const tabs = [
  {
    name: 'Details',
    value: 'details',
    label: __('Details'),
    iconLeft: DetailsIcon,
  },
  {
    name: 'Transactions',
    value: 'transactions',
    label: __('Transactions'),
    iconLeft: h(LucideArrowLeftRight, { class: 'h-4 w-4' }),
    count: computed(() => transactionsData.overall_count),
  },
  {
    name: 'Trades',
    value: 'trades',
    label: __('Trades'),
    iconLeft: h(LucideTrendingUp, { class: 'h-4 w-4' }),
    count: computed(() => tradesData.overall_count),
  },
]

const transactionPageLength = ref(20)
const transactionPeriod = ref('today')
const transactionDateFrom = ref('')
const transactionDateTo = ref('')
const transactionsData = reactive({
  rows: [],
  total_count: 0,
  overall_count: 0,
  deposits: 0,
  withdrawals: 0,
  aum: 0,
})

// one page at a time; `append` loads the next page below the current rows
let transactionsRequest = 0
async function loadTransactions(append = false) {
  const request = ++transactionsRequest
  const data = await call('crm.api.contact.get_linked_transactions', {
    contact: props.contactId,
    start: append ? transactionsData.rows.length : 0,
    page_length: transactionPageLength.value,
    period: transactionPeriod.value,
    date_from: transactionDateFrom.value || null,
    date_to: transactionDateTo.value || null,
  })
  // a newer filter change has already asked again; drop this late answer
  if (request !== transactionsRequest) return
  Object.assign(transactionsData, data, {
    rows: append ? [...transactionsData.rows, ...data.rows] : data.rows,
  })
}

loadTransactions()
watch(
  [
    transactionPageLength,
    transactionPeriod,
    transactionDateFrom,
    transactionDateTo,
  ],
  () => loadTransactions(),
)

const { getFormattedCurrency: getTransactionCurrency } =
  getMeta('CRM Transaction')

// amounts are signed: positive is a deposit, negative a withdrawal
function getTransactionType(amount) {
  if (amount > 0) return __('Deposit')
  if (amount < 0) return __('Withdrawal')
  return ''
}

const transactionRows = computed(() =>
  transactionsData.rows.map((row) => ({
    name: row.name,
    transaction_id: row.transaction_id,
    account_id: row.account_id,
    email: row.email,
    timestamp: timestampCell(row.timestamp),
    type: getTransactionType(row.amount),
    amount: getTransactionCurrency('amount', row),
  })),
)

const transactionSummary = computed(() => ({
  deposits: getTransactionCurrency('amount', {
    amount: transactionsData.deposits,
  }),
  withdrawals: getTransactionCurrency('amount', {
    amount: transactionsData.withdrawals,
  }),
  aum: getTransactionCurrency('amount', { amount: transactionsData.aum }),
}))

const transactionColumns = [
  { label: __('ID'), key: 'transaction_id', width: '10rem' },
  { label: __('Timestamp'), key: 'timestamp', width: '12rem' },
  { label: __('Type'), key: 'type', width: '7rem' },
  { label: __('Amount'), key: 'amount', align: 'right', width: '8rem' },
]

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
  transform: (data) => computed(() => getParsedSections(data)),
})

function getParsedSections(_sections) {
  return _sections.map((section) => {
    section.columns = section.columns.map((column) => {
      column.fields = column.fields.map((field) =>
        transformField(field, { showAddressModal }),
      )
      return column
    })
    return section
  })
}

const { showModal } = useDoctypeModal()

function showAddressModal(_address) {
  showModal({
    name: _address || null,
    doctype: 'Address',
    callbacks: {
      afterInsert: (d) => {
        capture('address_created')
        contact.doc.address = d.name
        contact.save.submit()
      },
    },
  })
}
</script>
