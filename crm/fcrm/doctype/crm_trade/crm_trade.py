# Copyright (c) 2026, Ajyad Capital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.client import flag_linked_clients


class CRMTrade(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		account_id: DF.Data | None
		commission: DF.Currency
		currency: DF.Link
		email: DF.Data | None
		price: DF.Currency
		quantity: DF.Float
		side: DF.Literal["Buy", "Sell"]
		symbol: DF.Data
		symbol_id: DF.Data
		timestamp: DF.Datetime
	# end: auto-generated types

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "Timestamp",
				"type": "Datetime",
				"key": "timestamp",
				"width": "9rem",
			},
			{
				"label": "Account ID",
				"type": "Data",
				"key": "account_id",
				"width": "8rem",
			},
			{
				"label": "Email",
				"type": "Data",
				"key": "email",
				"width": "11rem",
			},
			{
				"label": "Symbol ID",
				"type": "Data",
				"key": "symbol_id",
				"width": "8rem",
			},
			{
				"label": "Symbol",
				"type": "Data",
				"key": "symbol",
				"width": "7rem",
			},
			{
				"label": "Side",
				"type": "Select",
				"key": "side",
				"width": "5rem",
			},
			{
				"label": "Quantity",
				"type": "Float",
				"key": "quantity",
				"width": "6rem",
			},
			{
				"label": "Price",
				"type": "Currency",
				"key": "price",
				"width": "7rem",
			},
			{
				"label": "Currency",
				"type": "Link",
				"key": "currency",
				"width": "6rem",
			},
			{
				"label": "Commission",
				"type": "Currency",
				"key": "commission",
				"width": "7rem",
			},
		]
		rows = [
			"name",
			"timestamp",
			"account_id",
			"email",
			"symbol_id",
			"symbol",
			"side",
			"quantity",
			"price",
			"currency",
			"commission",
		]
		return {"columns": columns, "rows": rows}

	def validate(self):
		# Account ID and Email are how a trade is tied to a contact
		if not (self.account_id or self.email):
			frappe.throw(_("Either Account ID or Email is required to link the trade to a contact"))

	def on_update(self):
		flag_linked_clients(self)
