# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

import frappe

from crm.tests import CRMTestCase


def make_client(full_name, **values):
	return frappe.get_doc({"doctype": "CRM Client", "full_name": full_name, **values}).insert()


class TestCRMClient(CRMTestCase):
	def test_fields_default_sensibly(self):
		client = make_client("DefaultsClient", email="defaults@example.com", account_id="CLI-DEF")
		self.assertEqual((client.funded, client.traded), (0, 0))
		self.assertEqual(str(client.created_date), frappe.utils.nowdate())
		self.assertTrue(client.name.startswith("CLT-"))

	def test_email_and_account_id_are_unique(self):
		make_client("UniqueOne", email="unique@example.com", account_id="CLI-UNQ")
		with self.assertRaises(frappe.DuplicateEntryError):
			make_client("UniqueTwo", email="unique@example.com")
		with self.assertRaises(frappe.DuplicateEntryError):
			make_client("UniqueThree", account_id="CLI-UNQ")

	def test_clients_without_email_or_account_id_do_not_clash(self):
		make_client("BlankOne")
		make_client("BlankTwo")

	def test_email_must_be_valid(self):
		with self.assertRaises(frappe.ValidationError):
			make_client("BadEmail", email="not-an-email")

	def test_status_and_type_are_limited_to_their_options(self):
		for field, value in (("status", "Unknown"), ("type", "Visitor")):
			with self.assertRaises(frappe.ValidationError):
				make_client("BadOption", **{field: value})
		make_client("GoodOptions", status="Blocked", type="Employee")

	def test_contact_table_is_left_alone(self):
		# the point of a separate doctype: Ajyad data never lands on the shared Contact table
		contact_fields = {df.fieldname for df in frappe.get_meta("Contact").fields}
		self.assertFalse({f for f in contact_fields if f.startswith("ajyad_")})
