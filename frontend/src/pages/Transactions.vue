<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Transactions" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="listView?.customListActions"
        :actions="listView.customListActions"
      />
    </template>
  </LayoutHeader>
  <TransactionPeriodFilter
    v-if="timestampFilter"
    v-model:period="period"
    v-model:date-from="dateFrom"
    v-model:date-to="dateTo"
    class="mt-3"
  />
  <ViewControls
    v-if="timestampFilter"
    ref="viewControls"
    v-model="records"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Transaction"
    :filters="timestampFilter"
  />
  <TransactionSummaryCards
    v-if="records.data"
    class="mb-4 mt-3"
    v-bind="summary"
  />
  <RecordsListView
    v-if="records.data && rows.length"
    ref="listView"
    v-model="records.data.page_length_count"
    v-model:list="records"
    doctype="CRM Transaction"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: records.data.row_count,
      totalCount: records.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @applyFilter="(data) => viewControls?.applyFilter(data)"
    @selectionsChanged="
      (selections) => viewControls?.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="records.data && !rows.length"
    name="Transactions"
    :icon="LucideArrowLeftRight"
    :filtered="!!Object.keys(records.params?.filters || {}).length"
    :description="
      __('Deposits and withdrawals imported for your clients appear here.')
    "
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import RecordsListView from '@/components/ListViews/RecordsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import LucideArrowLeftRight from '~icons/lucide/arrow-left-right'
import { timestampCell } from '@/composables/useTimelinePreferences'
import TransactionPeriodFilter from '@/components/TransactionPeriodFilter.vue'
import TransactionSummaryCards from '@/components/TransactionSummaryCards.vue'
import { getMeta } from '@/stores/meta'
import { call } from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const listView = ref(null)

// records data is loaded in the ViewControls component
const records = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const { getFormattedCurrency } = getMeta('CRM Transaction')

// the list shows one period at a time, like the contact's Transactions tab; the
// server turns it into a timestamp filter so it uses the site timezone
const period = ref('today')
const dateFrom = ref('')
const dateTo = ref('')
const timestampFilter = ref(null)

let filterRequest = 0
async function loadTimestampFilter() {
  const request = ++filterRequest
  const filter = await call('crm.api.client.get_timestamp_filter', {
    period: period.value,
    date_from: dateFrom.value || null,
    date_to: dateTo.value || null,
  })
  if (request === filterRequest) timestampFilter.value = filter
}
loadTimestampFilter()
watch([period, dateFrom, dateTo], loadTimestampFilter)

// deposits, withdrawals and AUM of whatever the list is filtered to
const totals = reactive({ deposits: 0, withdrawals: 0, aum: 0 })
const summary = computed(() => ({
  deposits: getFormattedCurrency('amount', { amount: totals.deposits }),
  withdrawals: getFormattedCurrency('amount', { amount: totals.withdrawals }),
  aum: getFormattedCurrency('amount', { amount: totals.aum }),
}))

// the list reloads whenever its filters change, so refresh the totals with it
let totalsRequest = 0
watch(
  () => records.value?.data,
  async (data) => {
    if (!data) return
    const request = ++totalsRequest
    const result = await call('crm.fcrm.doctype.crm_transaction.crm_transaction.get_totals', {
      filters: { ...records.value.params?.filters, ...timestampFilter.value },
    })
    // a newer filter change has already asked again; drop this late answer
    if (request === totalsRequest) Object.assign(totals, result)
  },
)

function getValue(row, record) {
  if (row === 'timestamp') return timestampCell(record.timestamp)
  if (row === 'amount') return getFormattedCurrency('amount', record)
  return record[row]
}

const rows = computed(() => {
  const list = records.value?.data
  if (!list?.data || !['list', 'group_by'].includes(list.view_type)) return []
  return list.data.map((record) => {
    let _rows = {}
    list.rows.forEach((row) => {
      _rows[row] = getValue(row, record)
    })
    return _rows
  })
})

const columns = computed(() => {
  let _columns = records.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) =>
      index === _columns.length - 1 ? { ...col, align: 'right' } : col,
    )
  }

  return _columns
})
</script>
