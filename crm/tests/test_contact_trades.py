# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

import frappe
from frappe.utils import add_days, now_datetime

from crm.api.contact import get_linked_trades
from crm.tests import CRMTestCase


def make_contact(first_name, email, account_id=None):
	return frappe.get_doc(
		{
			"doctype": "Contact",
			"first_name": first_name,
			"email_ids": [{"email_id": email, "is_primary": 1}],
			"ajyad_account_id": account_id,
		}
	).insert()


def make_trade(account_id=None, email=None, timestamp="2026-01-01 10:00:00", **values):
	return frappe.get_doc(
		{
			"doctype": "CRM Trade",
			"account_id": account_id,
			"email": email,
			"timestamp": timestamp,
			"symbol_id": "SPUS.ARCA",
			"symbol": "STOCK",
			"quantity": 10,
			"price": 25.5,
			"currency": "USD",
			"side": "Buy",
			"commission": 1,
			**values,
		}
	).insert()


class TestContactTrades(CRMTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.contact = make_contact("TrdAlice", "trd-alice@example.com", "TRD-ACC-1")
		cls.other = make_contact("TrdBob", "trd-bob@example.com", "TRD-ACC-2")
		cls.trades = [
			make_trade(account_id="TRD-ACC-1", symbol_id="A.ARCA"),
			make_trade(email="trd-alice@example.com", symbol_id="B.ARCA"),
			make_trade(account_id="TRD-ACC-1", email="trd-alice@example.com", symbol_id="C.ARCA"),
			make_trade(account_id="TRD-ACC-2", symbol_id="D.ARCA"),
		]

		cls.period_contact = make_contact("TrdPeriod", "trd-period@example.com", "TRD-ACC-P")
		now = now_datetime()
		make_trade(account_id="TRD-ACC-P", symbol_id="TODAY", timestamp=now)
		make_trade(account_id="TRD-ACC-P", symbol_id="YEST", timestamp=add_days(now, -1))
		make_trade(account_id="TRD-ACC-P", symbol_id="OLD", timestamp=add_days(now, -90))

	def symbols(self, contact, **kwargs):
		return {row.symbol_id for row in get_linked_trades(contact.name, **kwargs)["rows"]}

	def test_matches_on_account_id_or_email(self):
		self.assertEqual(self.symbols(self.contact, period="all"), {"A.ARCA", "B.ARCA", "C.ARCA"})
		self.assertEqual(self.symbols(self.other, period="all"), {"D.ARCA"})

	def test_rows_carry_every_displayed_column(self):
		row = get_linked_trades(self.other.name, period="all")["rows"][0]
		self.assertEqual(
			(row.symbol_id, row.symbol, row.quantity, row.price, row.currency, row.side, row.commission),
			("D.ARCA", "STOCK", 10, 25.5, "USD", "Buy", 1),
		)

	def test_pages_cover_every_match(self):
		first = get_linked_trades(self.contact.name, start=0, page_length=2, period="all")
		second = get_linked_trades(self.contact.name, start=2, page_length=2, period="all")
		self.assertEqual(first["total_count"], 3)
		self.assertEqual([len(first["rows"]), len(second["rows"])], [2, 1])
		self.assertEqual(len({r.name for r in first["rows"] + second["rows"]}), 3)

	def test_defaults_to_today_and_counts_all_time(self):
		result = get_linked_trades(self.period_contact.name)
		self.assertEqual({r.symbol_id for r in result["rows"]}, {"TODAY"})
		self.assertEqual((result["total_count"], result["overall_count"]), (1, 3))

	def test_yesterday_and_all(self):
		self.assertEqual(self.symbols(self.period_contact, period="yesterday"), {"YEST"})
		self.assertEqual(len(self.symbols(self.period_contact, period="all")), 3)

	def test_contact_without_identifiers_has_no_trades(self):
		contact = frappe.get_doc({"doctype": "Contact", "first_name": "TrdNoIds"}).insert()
		self.assertEqual(
			get_linked_trades(contact.name, period="all"),
			{"rows": [], "total_count": 0, "overall_count": 0},
		)

	def test_trade_needs_account_id_or_email(self):
		with self.assertRaises(frappe.ValidationError):
			make_trade()

	def test_side_must_be_buy_or_sell(self):
		with self.assertRaises(frappe.ValidationError):
			make_trade(account_id="TRD-ACC-1", side="Hold")

	def test_quantity_price_and_commission_round_to_two_decimals(self):
		trade = make_trade(account_id="TRD-ACC-1", quantity=1.23456, price=9.876, commission=0.456)
		trade.reload()
		self.assertEqual((trade.quantity, trade.price, trade.commission), (1.23, 9.88, 0.46))


class TestFundedAndTradedFlags(CRMTestCase):
	def flags(self, contact):
		return tuple(frappe.db.get_value("Contact", contact.name, ["ajyad_funded", "ajyad_traded"]))

	def test_new_contact_starts_unticked(self):
		self.assertEqual(self.flags(make_contact("FlagNone", "flag-none@example.com", "FLAG-0")), (0, 0))

	def test_trade_ticks_traded_only_by_account_id(self):
		contact = make_contact("FlagAcc", "flag-acc@example.com", "FLAG-1")
		make_trade(account_id="FLAG-1")
		self.assertEqual(self.flags(contact), (0, 1))

	def test_transaction_ticks_funded_only_by_email(self):
		contact = make_contact("FlagMail", "flag-mail@example.com", "FLAG-2")
		frappe.get_doc(
			{
				"doctype": "CRM Transaction",
				"transaction_id": "FLAG-TXN-1",
				"email": "flag-mail@example.com",
				"timestamp": "2026-01-01 10:00:00",
				"amount": 5,
			}
		).insert()
		self.assertEqual(self.flags(contact), (1, 0))

	def test_other_contacts_are_untouched(self):
		other = make_contact("FlagOther", "flag-other@example.com", "FLAG-3")
		make_trade(account_id="FLAG-NOBODY")
		self.assertEqual(self.flags(other), (0, 0))

	def test_contact_created_after_its_records_is_ticked(self):
		make_trade(account_id="FLAG-4")
		self.assertEqual(self.flags(make_contact("FlagLate", "flag-late@example.com", "FLAG-4")), (0, 1))

	def test_deleting_the_record_does_not_untick(self):
		contact = make_contact("FlagKeep", "flag-keep@example.com", "FLAG-5")
		trade = make_trade(account_id="FLAG-5")
		trade.delete()
		self.assertEqual(self.flags(contact), (0, 1))
