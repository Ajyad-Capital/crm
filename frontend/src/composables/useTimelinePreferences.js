import { computed } from 'vue'
import { getConfig } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { formatDate, timeAgo } from '@/utils'
import { formatUtcTimestamp } from '@/utils/timestamps'

export function useTimelinePreferences() {
  const { _settings } = getSettings()

  const timestampFormat = computed(
    () => _settings.doc?.crm_timeline_timestamp_format || 'Relative',
  )
  const sortOrder = computed(
    () => _settings.doc?.crm_timeline_sort_order || 'Oldest First',
  )

  const showExactTimestamp = computed(() => timestampFormat.value === 'Exact')
  const isNewestFirst = computed(() => sortOrder.value === 'Newest First')

  return {
    timestampFormat,
    sortOrder,
    showExactTimestamp,
    isNewestFirst,
  }
}

// Builds a { label, timeAgo } cell for list/table views, honoring the global
// FCRM Settings timestamp format. `timeAgo` is the displayed value and `label`
// is the tooltip; when "Exact" is set the two are swapped so the date shows.
// Kept here (not in utils/index.js) so the settings store is not pulled into
// the eager import graph and fetched before frappe-ui is configured.
export function timestampCell(date) {
  if (!date) return { label: '', timeAgo: '' }
  const exact = formatDate(date)
  const relative = __(timeAgo(date))
  const showExact =
    getSettings()._settings.doc?.crm_timeline_timestamp_format === 'Exact'
  return {
    label: showExact ? relative : exact,
    timeAgo: showExact ? exact : relative,
  }
}

// A trade's timestamp is always shown as ISO 8601 UTC (e.g. 2026-11-20T15:23:38.500Z),
// whatever the timeline setting is; the relative time is the tooltip.
export function tradeTimestampCell(date) {
  if (!date) return { label: '', timeAgo: '' }
  return {
    label: __(timeAgo(date)),
    timeAgo: formatUtcTimestamp(date, getConfig('systemTimezone')),
  }
}
