from zoneinfo import ZoneInfo

from frappe.utils import get_datetime, get_system_timezone


def to_site_time(value):
	"""A timestamp with an explicit timezone, e.g. 2026-11-20T15:23:38.500Z, as site time.

	Datetime fields are stored in the site timezone, so values in another timezone (UTC from an
	import, for example) are converted. A value without a timezone is returned as it is.
	"""
	if not isinstance(value, str):
		return value

	try:
		parsed = get_datetime(value)
	except (ValueError, TypeError):
		return value

	if parsed.tzinfo is None:
		return value

	return parsed.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
