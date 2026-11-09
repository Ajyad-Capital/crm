# Copyright (c) 2026, Ajyad Capital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crm.api.contact import flag_linked_contacts


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

	def validate(self):
		# Account ID and Email are how a trade is tied to a contact
		if not (self.account_id or self.email):
			frappe.throw(_("Either Account ID or Email is required to link the trade to a contact"))

	def on_update(self):
		flag_linked_contacts(self)
