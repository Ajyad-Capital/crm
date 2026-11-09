import json

import frappe

from crm.install import (
	add_contact_custom_fields,
	add_contact_fields_to_layouts,
	add_contact_property_setters,
)

# Core Contact fields Ajyad doesn't use; hidden from the Contact layouts (the fields stay on the doctype)
REMOVED_FIELDS = {"salutation", "last_name", "gender", "company_name", "designation", "address"}
LAYOUTS = ["Contact-Quick Entry", "Contact-Side Panel"]


def remove_fields_from_layouts():
	for name in LAYOUTS:
		if not frappe.db.exists("CRM Fields Layout", name):
			continue

		doc = frappe.get_doc("CRM Fields Layout", name)
		layout = json.loads(doc.layout or "[]")

		for section in layout:
			for column in section.get("columns", []):
				column["fields"] = [f for f in column.get("fields") or [] if f not in REMOVED_FIELDS]
			# drop columns, then sections, left with nothing to show
			section["columns"] = [c for c in section.get("columns", []) if c["fields"]]
		layout = [s for s in layout if s.get("columns")]

		doc.layout = json.dumps(layout)
		doc.save()


def update_quick_filters():
	"""Swap the core Contact `status` quick filter for Ajyad's Status and add Account ID."""
	name = frappe.db.get_value("CRM Global Settings", {"dt": "Contact"})
	if not name:
		return

	doc = frappe.get_doc("CRM Global Settings", name)
	filters = ["ajyad_status" if f == "status" else f for f in json.loads(doc.json or "[]")]
	for fieldname in ("ajyad_status", "ajyad_account_id"):
		if fieldname not in filters:
			filters.append(fieldname)

	doc.json = json.dumps(list(dict.fromkeys(filters)))
	doc.save()


def execute():
	add_contact_custom_fields()
	add_contact_property_setters()
	add_contact_fields_to_layouts()
	remove_fields_from_layouts()
	update_quick_filters()

	# Contacts created before this field existed get their original creation date
	frappe.db.sql(
		"""
		UPDATE `tabContact`
		SET ajyad_created_date = DATE(creation)
		WHERE ajyad_created_date IS NULL
		"""
	)
