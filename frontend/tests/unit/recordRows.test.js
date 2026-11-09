import {
  formatCommission,
  formatDecimal,
  formatPrice,
  formatQuantity,
  getTradeValue,
} from '@/utils/recordRows'

describe('recordRows', () => {
  it('formats numbers to a fixed number of decimals', () => {
    expect(formatDecimal(1234.5, 2)).toBe('1,234.50')
    expect(formatDecimal(null, 2)).toBe('0.00')
  })

  it('shows quantity, price and commission with 2 decimals and no symbol', () => {
    expect(formatQuantity(12.5)).toBe('12.50')
    expect(formatPrice(1234.5)).toBe('1,234.50')
    expect(formatCommission(2)).toBe('2.00')
  })

  it('formats only the numeric trade columns', () => {
    const trade = { quantity: 50, price: 9.876, commission: 0.5, symbol: 'STOCK' }
    expect(getTradeValue('quantity', trade)).toBe('50.00')
    expect(getTradeValue('price', trade)).toBe('9.88')
    expect(getTradeValue('commission', trade)).toBe('0.50')
    expect(getTradeValue('symbol', trade)).toBe('STOCK')
  })
})
