# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

import frappe

from crm.api.contact import get_status_counts
from crm.tests import CRMTestCase


def make_contact(first_name, account_id, status):
	return frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": first_name,
			"email_ids": [{"email_id": f"{account_id.lower()}@example.com", "is_primary": 1}],
			"ajyad_account_id": account_id,
			"ajyad_status": status,
		}
	).insert()


class TestContactStatusCounts(CRMTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		for index, status in enumerate(["Approved", "Approved", "Rejected", "Pending", "Blocked", "Blocked", None]):
			make_contact(f"StatusCount{index}", f"STC-{index}", status)

	def test_counts_each_status_among_the_filtered_contacts(self):
		counts = get_status_counts({"ajyad_account_id": ["like", "STC-%"]})
		self.assertEqual(counts, {"Approved": 2, "Rejected": 1, "Pending": 1, "Blocked": 2})

	def test_other_filters_narrow_the_counts(self):
		counts = get_status_counts('{"ajyad_account_id": ["in", ["STC-0", "STC-2", "STC-4"]]}')
		self.assertEqual(counts, {"Approved": 1, "Rejected": 1, "Pending": 0, "Blocked": 1})

	def test_a_status_filter_is_ignored(self):
		counts = get_status_counts({"ajyad_account_id": ["like", "STC-%"], "ajyad_status": "Blocked"})
		self.assertEqual(counts, {"Approved": 2, "Rejected": 1, "Pending": 1, "Blocked": 2})

	def test_no_matches_gives_zeroes(self):
		self.assertEqual(
			get_status_counts({"ajyad_account_id": "STC-NONE"}),
			{"Approved": 0, "Rejected": 0, "Pending": 0, "Blocked": 0},
		)

	def test_blocked_is_a_valid_status(self):
		contact = make_contact("StatusBlockedOk", "BLK-OK", "Blocked")
		self.assertEqual(contact.ajyad_status, "Blocked")
