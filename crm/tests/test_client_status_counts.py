# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

import frappe

from crm.api.client import get_status_counts
from crm.tests import CRMTestCase


def make_client(full_name, account_id, status):
	return frappe.get_doc(
		{
			"doctype": "CRM Client",
			"full_name": full_name,
			"email": f"{account_id.lower()}@example.com",
			"account_id": account_id,
			"status": status,
		}
	).insert()


class TestClientStatusCounts(CRMTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for index, status in enumerate(["Approved", "Approved", "Rejected", "Pending", "Blocked", "Blocked", None]):
			make_client(f"StatusCount{index}", f"STC-{index}", status)

	def test_counts_each_status_among_the_filtered_clients(self):
		counts = get_status_counts({"account_id": ["like", "STC-%"]})
		self.assertEqual(counts, {"Approved": 2, "Rejected": 1, "Pending": 1, "Blocked": 2})

	def test_other_filters_narrow_the_counts(self):
		counts = get_status_counts('{"account_id": ["in", ["STC-0", "STC-2", "STC-4"]]}')
		self.assertEqual(counts, {"Approved": 1, "Rejected": 1, "Pending": 0, "Blocked": 1})

	def test_a_status_filter_is_ignored(self):
		counts = get_status_counts({"account_id": ["like", "STC-%"], "status": "Blocked"})
		self.assertEqual(counts, {"Approved": 2, "Rejected": 1, "Pending": 1, "Blocked": 2})

	def test_no_matches_gives_zeroes(self):
		self.assertEqual(
			get_status_counts({"account_id": "STC-NONE"}),
			{"Approved": 0, "Rejected": 0, "Pending": 0, "Blocked": 0},
		)
