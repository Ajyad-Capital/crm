import { computed, reactive, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import { timestampCell } from '@/composables/useTimelinePreferences'
import {
  formatCommission,
  formatPrice,
  formatQuantity,
} from '@/utils/recordRows'

// A contact's trades, one server-side page at a time, narrowed by a period
export function useLinkedTrades(contactId) {
  const pageLength = ref(20)
  const period = ref('today')
  const dateFrom = ref('')
  const dateTo = ref('')
  const data = reactive({ rows: [], total_count: 0, overall_count: 0 })

  // `append` loads the next page below the current rows
  let latestRequest = 0
  async function load(append = false) {
    const request = ++latestRequest
    const result = await call('crm.api.client.get_linked_trades', {
      client: contactId,
      start: append ? data.rows.length : 0,
      page_length: pageLength.value,
      period: period.value,
      date_from: dateFrom.value || null,
      date_to: dateTo.value || null,
    })
    // a newer filter change has already asked again; drop this late answer
    if (request !== latestRequest) return
    Object.assign(data, result, {
      rows: append ? [...data.rows, ...result.rows] : result.rows,
    })
  }

  load()
  watch([pageLength, period, dateFrom, dateTo], () => load())

  // Account ID and Email only link trades to the contact, so they aren't shown
  const rows = computed(() =>
    data.rows.map((row) => ({
      name: row.name,
      symbol_id: row.symbol_id,
      symbol: row.symbol,
      side: __(row.side),
      quantity: formatQuantity(row.quantity),
      price: formatPrice(row.price),
      currency: row.currency,
      commission: formatCommission(row.commission),
      timestamp: timestampCell(row.timestamp),
    })),
  )

  const columns = [
    { label: __('Timestamp'), key: 'timestamp', width: '13.5rem' },
    { label: __('Symbol ID'), key: 'symbol_id', width: '8rem' },
    { label: __('Symbol'), key: 'symbol', width: '6rem' },
    { label: __('Side'), key: 'side', width: '4rem' },
    { label: __('Quantity'), key: 'quantity', align: 'right', width: '7rem' },
    { label: __('Price'), key: 'price', align: 'right', width: '8rem' },
    { label: __('Currency'), key: 'currency', width: '5rem' },
    {
      label: __('Commission'),
      key: 'commission',
      align: 'right',
      width: '7rem',
    },
  ]

  return { data, rows, columns, pageLength, period, dateFrom, dateTo, load }
}
