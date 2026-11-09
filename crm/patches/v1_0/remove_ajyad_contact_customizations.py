import json

import frappe

AJYAD_FIELDS = (
	"ajyad_account_id",
	"ajyad_type",
	"ajyad_status",
	"ajyad_id_card_number",
	"ajyad_passport_number",
	"ajyad_exit_point",
	"ajyad_funded",
	"ajyad_traded",
	"ajyad_created_date",
)

STOCK_LAYOUTS = {
	"Contact-Quick Entry": '[{"name": "salutation_section", "columns": [{"name": "column_eXks", "fields": ["salutation"]}]}, {"name": "full_name_section", "hideBorder": true, "columns": [{"name": "column_cSxf", "fields": ["first_name"]}, {"name": "column_yBc7", "fields": ["last_name"]}]}, {"name": "email_section", "hideBorder": true, "columns": [{"name": "column_tH3L", "fields": ["email_id"]}]}, {"name": "mobile_gender_section", "hideBorder": true, "columns": [{"name": "column_lrfI", "fields": ["mobile_no"]}, {"name": "column_Tx3n", "fields": ["gender"]}]}, {"name": "organization_section", "hideBorder": true, "columns": [{"name": "column_S0J8", "fields": ["company_name"]}]}, {"name": "designation_section", "hideBorder": true, "columns": [{"name": "column_bsO8", "fields": ["designation"]}]}, {"name": "address_section", "hideBorder": true, "columns": [{"name": "column_W3VY", "fields": ["address"]}]}]',
	"Contact-Side Panel": '[{"label": "Details", "name": "details_section", "opened": true, "columns": [{"name": "column_eIWl", "fields": ["salutation", "first_name", "last_name", "email_id", "mobile_no", "gender", "company_name", "designation", "address"]}]}]',
}


def uncopied_contacts():
	"""Contacts with Ajyad data that have no CRM Client yet.

	The created date is filled in on every new Contact, so it doesn't count as Ajyad data.
	"""
	marker_fields = [field for field in AJYAD_FIELDS if field != "ajyad_created_date"]
	has_data = " OR ".join(f"IFNULL(`{field}`, '') NOT IN ('', '0')" for field in marker_fields)
	contacts = frappe.db.sql(
		f"SELECT name, email_id, ajyad_account_id FROM `tabContact` WHERE {has_data}", as_dict=True
	)

	missing = []
	for contact in contacts:
		found = (
			contact.ajyad_account_id
			and frappe.db.exists("CRM Client", {"account_id": contact.ajyad_account_id})
		) or (contact.email_id and frappe.db.exists("CRM Client", {"email": contact.email_id}))
		if not found:
			missing.append(contact.name)
	return missing


def execute():
	"""Take the Ajyad additions off Contact so it is stock again for Helpdesk and the rest of Frappe.

	Runs only once every contact with Ajyad data has a CRM Client, because removing the custom
	fields drops their values from Contact.
	"""
	if frappe.db.has_column("Contact", "ajyad_account_id"):
		missing = uncopied_contacts()
		if missing:
			frappe.log_error(
				title="Ajyad Contact customizations kept",
				message=f"These contacts have no CRM Client yet: {', '.join(missing)}",
			)
			print(f"Kept the Ajyad fields on Contact: {len(missing)} contacts are not copied yet")  # noqa: T201
			return

	for fieldname in AJYAD_FIELDS:
		name = frappe.db.get_value("Custom Field", {"dt": "Contact", "fieldname": fieldname})
		if name:
			frappe.delete_doc("Custom Field", name, force=True)

	for setter in frappe.get_all(
		"Property Setter",
		filters={"doc_type": "Contact", "field_name": "first_name", "property": "label", "value": "Full Name"},
		pluck="name",
	):
		frappe.delete_doc("Property Setter", setter, force=True)

	for name, layout in STOCK_LAYOUTS.items():
		if frappe.db.exists("CRM Fields Layout", name):
			frappe.db.set_value("CRM Fields Layout", name, "layout", layout)

	settings = frappe.db.get_value("CRM Global Settings", {"dt": "Contact"})
	if settings:
		frappe.db.set_value("CRM Global Settings", settings, "json", json.dumps(["status", "email_id", "phone"]))

	frappe.clear_cache(doctype="Contact")
