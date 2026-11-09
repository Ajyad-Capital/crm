<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Trades" />
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
    doctype="CRM Trade"
    :filters="timestampFilter"
  />
  <TradeSummaryCards
    v-if="records.data"
    class="mb-4 mt-3"
    :total-trades="records.data.total_count"
  />
  <RecordsListView
    v-if="records.data && rows.length"
    ref="listView"
    v-model="records.data.page_length_count"
    v-model:list="records"
    doctype="CRM Trade"
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
    name="Trades"
    :icon="LucideTrendingUp"
    :filtered="!!Object.keys(records.params?.filters || {}).length"
    :description="
      __('Trades imported for your clients appear here.')
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
import LucideTrendingUp from '~icons/lucide/trending-up'
import { timestampCell } from '@/composables/useTimelinePreferences'
import TradeSummaryCards from '@/components/TradeSummaryCards.vue'
import TransactionPeriodFilter from '@/components/TransactionPeriodFilter.vue'
import { call } from 'frappe-ui'
import { getTradeValue } from '@/utils/recordRows'
import { computed, ref, watch } from 'vue'

const listView = ref(null)

// records data is loaded in the ViewControls component
const records = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

// the list shows one period at a time, like the contact's Trades tab; the
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

function getValue(row, record) {
  if (row === 'timestamp') return timestampCell(record.timestamp)
  return getTradeValue(row, record)
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
