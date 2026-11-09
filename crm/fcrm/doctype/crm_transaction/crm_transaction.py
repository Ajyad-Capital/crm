# Copyright (c) 2026, Ajyad Capital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


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

	def validate(self):
		# Account ID and Email are how a transaction is tied to a contact
		if not (self.account_id or self.email):
			frappe.throw(_("Either Account ID or Email is required to link the transaction to a contact"))
