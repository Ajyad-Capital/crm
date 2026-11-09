# import frappe
from frappe.contacts.doctype.contact.contact import Contact


class CustomContact(Contact):
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Name",
				"type": "Data",
				"key": "full_name",
				"width": "17rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email_id",
				"width": "12rem",
			},
			{
				"label": "Phone",
				"type": "Data",
				"key": "mobile_no",
				"width": "12rem",
			},
			{
				"label": "Account ID",
				"type": "Data",
				"key": "ajyad_account_id",
				"width": "12rem",
			},
			{
				"label": "Type",
				"type": "Select",
				"key": "ajyad_type",
				"width": "8rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "ajyad_status",
				"width": "8rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"full_name",
			"ajyad_account_id",
			"ajyad_type",
			"ajyad_status",
			"email_id",
			"mobile_no",
			"modified",
			"image",
		]
		return {"columns": columns, "rows": rows}
