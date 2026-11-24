# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

from datetime import datetime
from zoneinfo import ZoneInfo

from frappe.utils import get_system_timezone

from crm.overrides.data_import import ISO_TIMESTAMP_WITH_ZONE
from crm.tests import CRMTestCase
from crm.utils.timezones import to_site_time


class TestToSiteTime(CRMTestCase):
	def test_utc_value_is_converted_to_the_site_timezone(self):
		expected = (
			datetime(2026, 2, 2, 14, 30, 15, 125000, tzinfo=ZoneInfo("UTC"))
			.astimezone(ZoneInfo(get_system_timezone()))
			.replace(tzinfo=None)
		)
		self.assertEqual(to_site_time("2026-02-02T14:30:15.125Z"), expected)

	def test_offset_value_is_converted_too(self):
		self.assertEqual(
			to_site_time("2026-02-02T14:30:15+00:00"), to_site_time("2026-02-02T14:30:15Z")
		)

	def test_value_without_a_timezone_is_unchanged(self):
		self.assertEqual(to_site_time("2026-02-02 14:30:15"), "2026-02-02 14:30:15")
		self.assertEqual(to_site_time(None), None)

	def test_invalid_value_is_unchanged(self):
		self.assertEqual(to_site_time("not a date"), "not a date")


class TestImportTimestampPattern(CRMTestCase):
	def test_matches_iso_values_with_a_timezone_only(self):
		for value in ("2026-02-02T14:30:15.125Z", "2026-02-02T14:30:15Z", "2026-02-02T14:30:15+03:00"):
			self.assertTrue(ISO_TIMESTAMP_WITH_ZONE.match(value), value)
		for value in ("2026-02-02T14:30:15", "2026-02-02 14:30:15", "02-02-2026"):
			self.assertFalse(ISO_TIMESTAMP_WITH_ZONE.match(value), value)
