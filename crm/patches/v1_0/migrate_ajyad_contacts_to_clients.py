import frappe

from crm.install import add_default_fields_layout, add_default_quick_filters

# Ajyad custom field on Contact -> field on CRM Client
FIELD_MAP = {
	"ajyad_account_id": "account_id",
	"ajyad_type": "type",
	"ajyad_status": "status",
	"ajyad_id_card_number": "id_card_number",
	"ajyad_passport_number": "passport_number",
	"ajyad_exit_point": "exit_point",
	"ajyad_funded": "funded",
	"ajyad_traded": "traded",
	"ajyad_created_date": "created_date",
}


# created_date is filled in automatically on every new Contact, so it says nothing about
# whether the contact is an Ajyad client
MARKER_FIELDS = [field for field in FIELD_MAP if field != "ajyad_created_date"]


def execute():
	"""Copy contacts that carry Ajyad data into CRM Client.

	Contacts are only read, never changed or deleted, so Helpdesk and the rest of Frappe keep
	their records. The Contact customisations are removed by remove_ajyad_contact_customizations.
	"""
	# layouts and quick filters for the new doctype on sites that were installed before it existed
	add_default_fields_layout()
	add_default_quick_filters()

	if not frappe.db.has_column("Contact", "ajyad_account_id"):
		return

	has_data = " OR ".join(f"IFNULL(`{field}`, '') NOT IN ('', '0')" for field in MARKER_FIELDS)
	contacts = frappe.db.sql(
		f"""
		SELECT name, first_name, last_name, email_id, mobile_no, phone, image, creation,
			{", ".join(f"`{field}`" for field in FIELD_MAP)}
		FROM `tabContact`
		WHERE {has_data}
		ORDER BY creation
		""",
		as_dict=True,
	)

	copied = skipped = 0
	for contact in contacts:
		account_id = contact.ajyad_account_id or None
		email = contact.email_id or None

		if (account_id and frappe.db.exists("CRM Client", {"account_id": account_id})) or (
			email and frappe.db.exists("CRM Client", {"email": email})
		):
			skipped += 1
			continue

		client = frappe.get_doc(
			{
				"doctype": "CRM Client",
				"full_name": " ".join(filter(None, [contact.first_name, contact.last_name])) or contact.name,
				"email": email,
				"phone": contact.mobile_no or contact.phone,
				"image": contact.image,
				**{new: contact[old] for old, new in FIELD_MAP.items() if new != "created_date"},
				"created_date": contact.ajyad_created_date or str(contact.creation)[:10],
			}
		)
		try:
			client.insert(ignore_permissions=True)
		except Exception:
			frappe.log_error(title=f"Could not copy contact {contact.name} to CRM Client")
			skipped += 1
			continue

		frappe.db.set_value("CRM Client", client.name, "creation", contact.creation, update_modified=False)
		copied += 1

	print(f"Copied {copied} contacts to CRM Client, skipped {skipped}")  # noqa: T201
