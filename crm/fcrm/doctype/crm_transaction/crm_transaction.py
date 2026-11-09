# Copyright (c) 2026, Ajyad Capital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from crm.api.contact import flag_linked_contacts


class CRMTransaction(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_id: DF.Data | None
		amount: DF.Currency
		email: DF.Data | None
		timestamp: DF.Datetime
		transaction_id: DF.Data
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "ID",
				"type": "Data",
				"key": "transaction_id",
				"width": "14rem",
			},
			{
				"label": "Timestamp",
				"type": "Datetime",
				"key": "timestamp",
				"width": "12rem",
			},
			{
				"label": "Account ID",
				"type": "Data",
				"key": "account_id",
				"width": "10rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "14rem",
			},
			{
				"label": "Amount",
				"type": "Currency",
				"key": "amount",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"transaction_id",
			"timestamp",
			"account_id",
			"email",
			"amount",
		]
		return {"columns": columns, "rows": rows}

	def validate(self):
		# Account ID and Email are how a transaction is tied to a contact
		if not (self.account_id or self.email):
			frappe.throw(_("Either Account ID or Email is required to link the transaction to a contact"))

	def on_update(self):
		flag_linked_contacts(self)


@frappe.whitelist()
def get_totals(filters: str | dict | None = None):
	"""Deposits, withdrawals and AUM (deposits - withdrawals) of the transactions matching `filters`.

	`filters` is a list view filter dict, e.g. {"account_id": "ACC-1", "timestamp": ["between", [a, b]]}.
	Amounts are signed: a positive amount is a deposit and a negative one a withdrawal.
	get_list applies the transaction permissions of the current user.
	"""
	filters = frappe.parse_json(filters) or {}
	if not isinstance(filters, dict):
		frappe.throw(_("Invalid filters"))

	conditions = [
		[fieldname, *value] if isinstance(value, list) else [fieldname, "=", value]
		for fieldname, value in filters.items()
	]

	def total(*extra):
		result = frappe.get_list(
			"CRM Transaction",
			filters=[*conditions, *extra],
			fields=[{"SUM": "amount", "as": "value"}],
		)
		return flt(result[0].value) if result else 0

	deposits = total(["amount", ">", 0])
	withdrawals = abs(total(["amount", "<", 0]))

	return {"deposits": deposits, "withdrawals": withdrawals, "aum": deposits - withdrawals}
