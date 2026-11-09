import frappe

from crm.install import CONTACT_CUSTOM_FIELDS


def execute():
	"""Add Blocked to the Contact Status options on sites where the field already exists."""
	options = next(f["options"] for f in CONTACT_CUSTOM_FIELDS if f["fieldname"] == "ajyad_status")

	name = frappe.db.get_value("Custom Field", {"dt": "Contact", "fieldname": "ajyad_status"})
	if not name:
		return

	frappe.db.set_value("Custom Field", name, "options", options)
	frappe.clear_cache(doctype="Contact")
