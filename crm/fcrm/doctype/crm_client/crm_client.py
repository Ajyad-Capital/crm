# Copyright (c) 2026, Ajyad Capital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.client import sync_funded_and_traded


class CRMClient(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_id: DF.Data | None
		created_date: DF.Date | None
		email: DF.Data | None
		exit_point: DF.Data | None
		full_name: DF.Data
		funded: DF.Check
		id_card_number: DF.Data | None
		image: DF.AttachImage | None
		passport_number: DF.Data | None
		phone: DF.Data | None
		status: DF.Literal["", "Approved", "Rejected", "Pending", "Blocked"]
		traded: DF.Check
		type: DF.Literal["", "Employee", "Client"]
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		columns = [
			{"label": "Name", "type": "Data", "key": "full_name", "width": "17rem"},
			{"label": "Email", "type": "Data", "key": "email", "width": "12rem"},
			{"label": "Phone", "type": "Data", "key": "phone", "width": "12rem"},
			{"label": "Account ID", "type": "Data", "key": "account_id", "width": "12rem"},
			{"label": "Type", "type": "Select", "key": "type", "width": "8rem"},
			{"label": "Status", "type": "Select", "key": "status", "width": "8rem"},
			{"label": "Created Date", "type": "Date", "key": "created_date", "width": "10rem"},
			{"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
		]
		rows = [
			"name",
			"full_name",
			"image",
			"email",
			"phone",
			"account_id",
			"type",
			"status",
			"created_date",
			"modified",
		]
		return {"columns": columns, "rows": rows}

	def validate(self):
		self.validate_unique_identifiers()
		sync_funded_and_traded(self)

	def validate_unique_identifiers(self):
		"""Email and Account ID identify a client, so neither can be shared between clients.

		Checked with a readable message before the database's unique index would object. Only
		when the value is new or changed, so existing duplicates don't block unrelated edits.
		"""
		for fieldname, label in (("email", _("Email")), ("account_id", _("Account ID"))):
			value = self.get(fieldname)
			if not value or not (self.is_new() or self.has_value_changed(fieldname)):
				continue

			duplicate = frappe.db.exists("CRM Client", {fieldname: value, "name": ["!=", self.name]})
			if duplicate:
				frappe.throw(
					_("{0} {1} is already used by client {2}").format(label, value, duplicate),
					frappe.DuplicateEntryError,
				)
