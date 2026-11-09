// Cell values for the Transactions and Trades list pages. Timestamps and the
// transaction amount are formatted by the page (they need the settings store
// and the doctype meta), everything else is here.

export function formatDecimal(value, digits = 2) {
  return Number(value || 0).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

export const formatQuantity = (value) => formatDecimal(value, 2)

// the Currency column already says which currency, so no symbol here
export const formatPrice = (value) => formatDecimal(value, 2)
export const formatCommission = (value) => formatDecimal(value, 2)

export function getTradeValue(key, trade) {
  if (key === 'quantity') return formatQuantity(trade.quantity)
  if (key === 'price') return formatPrice(trade.price)
  if (key === 'commission') return formatCommission(trade.commission)
  return trade[key]
}
