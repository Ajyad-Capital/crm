import frappe

from crm.api.contact import ACTIVITY_FLAGS, flag_linked_contacts


def execute():
	"""Tick Funded / Traded for contacts whose transactions / trades were recorded before the automation."""
	for doctype in ACTIVITY_FLAGS.values():
		pairs = frappe.get_all(doctype, fields=["account_id", "email"], distinct=True)
		for pair in pairs:
			flag_linked_contacts(frappe._dict(doctype=doctype, account_id=pair.account_id, email=pair.email))
