import { dayjs } from 'frappe-ui'

// Server datetimes are wall-clock values in the site (system) timezone. Shows one as an
// ISO 8601 UTC timestamp, e.g. 2026-11-20T15:23:38.500Z.
export function formatUtcTimestamp(value, systemTimezone) {
  if (!value || !dayjs(value).isValid()) return ''
  const parsed = systemTimezone ? dayjs.tz(value, systemTimezone) : dayjs(value)
  return parsed.utc().format('YYYY-MM-DDTHH:mm:ss.SSS[Z]')
}
