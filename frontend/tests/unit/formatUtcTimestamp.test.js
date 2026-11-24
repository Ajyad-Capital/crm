import { describe, it, expect } from 'vitest'
import { formatUtcTimestamp } from '@/utils/timestamps'

describe('formatUtcTimestamp', () => {
  it('converts a site-timezone value to UTC with milliseconds', () => {
    expect(
      formatUtcTimestamp('2026-11-20 18:23:38.500000', 'Asia/Bahrain'),
    ).toBe('2026-11-20T15:23:38.500Z')
  })

  it('keeps the date right when the conversion crosses midnight', () => {
    expect(formatUtcTimestamp('2026-11-21 01:00:00', 'Asia/Bahrain')).toBe(
      '2026-11-20T22:00:00.000Z',
    )
  })

  it('truncates microseconds to milliseconds', () => {
    expect(
      formatUtcTimestamp('2026-11-09 15:29:56.388755', 'Asia/Bahrain'),
    ).toBe('2026-11-09T12:29:56.388Z')
  })

  it('returns an empty string for empty or invalid values', () => {
    expect(formatUtcTimestamp('', 'Asia/Bahrain')).toBe('')
    expect(formatUtcTimestamp(null, 'Asia/Bahrain')).toBe('')
    expect(formatUtcTimestamp('not a date', 'Asia/Bahrain')).toBe('')
  })
})
