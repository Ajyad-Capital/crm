<template>
  <div v-if="contact.doc" ref="parentRef" class="flex h-full">
    <Resizer
      v-if="contact.doc"
      :parent="$refs.parentRef"
      class="flex h-full flex-col overflow-hidden border-r"
    >
      <div class="border-b">
        <FileUploader
          :validateFile="validateIsImageFile"
          @success="changeContactImage"
        >
          <template #default="{ openFileSelector, error }">
            <div class="flex flex-col items-start justify-start gap-4 p-5">
              <div class="flex gap-4 items-center">
                <div class="group relative h-15.5 w-15.5">
                  <Avatar
                    size="3xl"
                    class="h-15.5 w-15.5"
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
                      class="z-1 absolute bottom-0 left-0 right-0 flex h-14 cursor-pointer items-center justify-center rounded-b-full bg-black bg-opacity-40 pt-5 opacity-0 duration-300 ease-in-out group-hover:opacity-100"
                      style="
                        -webkit-clip-path: inset(22px 0 0 0);
                        clip-path: inset(22px 0 0 0);
                      "
                    >
                      <CameraIcon class="h-6 w-6 cursor-pointer text-white" />
                    </div>
                  </component>
                </div>
                <div class="flex flex-col gap-2 truncate text-ink-gray-9">
                  <div class="truncate text-3xl-medium">
                    <span v-if="contact.doc.salutation">
                      {{ contact.doc.salutation + ' ' }}
                    </span>
                    <span>{{ contact.doc.full_name }}</span>
                  </div>
                  <div
                    v-if="contact.doc.company_name"
                    class="flex items-center gap-1.5 text-base text-ink-gray-8"
                  >
                    {{ contact.doc.company_name }}
                  </div>
                  <ErrorMessage :message="__(error)" />
                </div>
              </div>
              <div class="flex gap-1.5">
                <Button
                  v-if="callEnabled && contact.doc.mobile_no"
                  :label="__('Make Call')"
                  size="sm"
                  :iconLeft="PhoneIcon"
                  @click="callEnabled && makeCall(contact.doc.mobile_no)"
                />
                <Button
                  v-if="canDelete"
                  :label="__('Delete')"
                  theme="red"
                  size="sm"
                  iconLeft="lucide-trash-2"
                  @click="deleteContact()"
                />
              </div>
            </div>
          </template>
        </FileUploader>
      </div>
      <div
        v-if="sections.data"
        class="flex flex-1 flex-col justify-between overflow-hidden"
      >
        <SidePanelLayout
          :sections="parsedSections"
          doctype="Contact"
          :docname="contact.doc.name"
          @reload="sections.reload"
        />
      </div>
    </Resizer>
    <Tabs
      v-model="activeTab"
      as="div"
      :tabs="tabs"
      class="flex flex-1 overflow-hidden flex-col [&_[role='tab']]:px-1 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-5 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-[22px] [&>[role='tabpanel']:not([hidden])]:flex [&>[role='tabpanel']:not([hidden])]:grow [&>[data-slot=tab-list]]:overflow-x-auto [&_[data-slot=tab-indicator]]:translate-y-0 [&>[data-slot=tab-panel]]:min-h-0 [&>[data-slot=tab-panel]]:flex-col [&>[data-slot=tab-panel]]:overflow-auto"
    >
      <template #tab-label="{ tab }">{{ __(tab.label) }}</template>
      <template #tab-suffix="{ tab, active }">
        <Badge
          :class="[active ? 'bg-surface-gray-10' : 'bg-gray-600']"
          variant="solid"
          theme="gray"
          size="sm"
        >
          {{ tab.count }}
        </Badge>
      </template>
      <template #tab-panel="{ tab }">
        <template v-if="tab.value === 'transactions'">
          <template v-if="transactionsData.overall_count">
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
          <EmptyState
            v-else
            :icon="tab.iconLeft"
            name="Transactions"
            :description="
              __('No transactions match this contact\'s Account ID or email.')
            "
          />
        </template>

        <EmptyState
          v-else
          :icon="tab.iconLeft"
          :name="tab.label"
          :description="__('Nothing to show for this contact yet.')"
        />
      </template>
    </Tabs>
  </div>
  <ErrorPage
    v-else-if="errorTitle"
    :errorTitle="errorTitle"
    :errorMessage="errorMessage"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteLinkedDocModal"
    v-model="showDeleteLinkedDocModal"
    :doctype="'Contact'"
    :docname="contact.doc.name"
    name="Contacts"
  />
</template>

<script setup>
import ErrorPage from '@/components/ErrorPage.vue'
import Resizer from '@/components/Resizer.vue'
import SidePanelLayout from '@/components/SidePanelLayout.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import TransactionsListView from '@/components/ListViews/TransactionsListView.vue'
import TransactionSummaryCards from '@/components/TransactionSummaryCards.vue'
import TransactionPeriodFilter from '@/components/TransactionPeriodFilter.vue'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import LucideTrendingUp from '~icons/lucide/trending-up'
import { validateIsImageFile, setupCustomizations } from '@/utils'
import { useContactFields } from '@/composables/useContactFields'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useDocument } from '@/data/document'
import { getSettings } from '@/stores/settings'
import { getMeta } from '@/stores/meta'
import { globalStore } from '@/stores/global.js'
import { callEnabled } from '@/composables/telephony'
import {
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
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '@/components/ListViews/EmptyState.vue'

const { brand } = getSettings()
const { makeCall, $dialog, $socket } = globalStore()

const { doctypeMeta } = getMeta('Contact')
const { capture } = useTelemetry()

const props = defineProps({
  contactId: { type: String, required: true },
})

const router = useRouter()

const errorTitle = ref('')
const errorMessage = ref('')

const {
  document: contact,
  permissions,
  scripts,
  triggerOnRender,
} = useDocument('Contact', props.contactId)

const canDelete = computed(() => permissions.data?.permissions?.delete || false)

const transformField = useContactFields(contact)

onMounted(async () => {
  if (contact.doc) await triggerOnRender()
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
const showDeleteLinkedDocModal = ref(false)

async function deleteContact() {
  showDeleteLinkedDocModal.value = true
}

function changeContactImage(file) {
  contact.doc.image = file?.file_url || ''
  contact.save.submit(null, {
    onSuccess: () => {
      toast.success(__('Contact image updated'))
    },
  })
}

const activeTab = ref('transactions')
const tabs = [
  {
    value: 'transactions',
    label: 'Transactions',
    iconLeft: LucideArrowLeftRight,
    count: computed(() => transactionsData.overall_count),
  },
  // placeholder until the Trades columns and data source are defined
  {
    value: 'trades',
    label: 'Trades',
    iconLeft: LucideTrendingUp,
    count: 0,
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
  { label: __('ID'), key: 'transaction_id', width: '14rem' },
  { label: __('Timestamp'), key: 'timestamp', width: '14rem' },
  { label: __('Type'), key: 'type', width: '10rem' },
  { label: __('Amount'), key: 'amount', align: 'right', width: '8rem' },
]

const sections = createResource({
  url: 'crm.fcrm.doctype.crm_fields_layout.crm_fields_layout.get_sidepanel_sections',
  cache: ['sidePanelSections', 'Contact'],
  params: { doctype: 'Contact' },
  auto: true,
})

const parsedSections = computed(() => {
  if (!sections.data) return []
  return sections.data.map((section) => ({
    ...section,
    columns: section.columns.map((column) => ({
      ...column,
      fields: column.fields.map((field) => {
        field.label = fieldLabelMap[field.fieldname] || field.label
        field.placeholder =
          fieldPlaceholderMap[field.fieldname] || field.placeholder
        return transformField(field, { showAddressModal })
      }),
    })),
  }))
})

const fieldLabelMap = {
  mobile_no: __('Mobile Number'),
  company_name: __('Organization'),
}

const fieldPlaceholderMap = {
  mobile_no: __('Add Mobile Number...'),
  company_name: __('Add Organization...'),
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

// Setup custom actions from Form Scripts
watch(
  () => contact.doc,
  async (_doc) => {
    if (scripts.data?.length) {
      let s = await setupCustomizations(scripts.data, {
        doc: _doc,
        $dialog,
        $socket,
        router,
        updateField: contact.setValue.submit,
        deleteDoc: deleteContact,
        call,
      })
      contact._actions = s.actions || []
    }
  },
  { once: true },
)
</script>
