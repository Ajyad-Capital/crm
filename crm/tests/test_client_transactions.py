# Copyright (c) 2026, Ajyad Capital and contributors
# See license.txt

import frappe

from frappe.utils import add_days, now_datetime, nowdate

from crm.api.client import get_linked_transactions
from crm.tests import CRMTestCase


def make_client(full_name, email=None, account_id=None, **values):
	return frappe.get_doc(
		{"doctype": "CRM Client", "full_name": full_name, "email": email, "account_id": account_id, **values}
	).insert()


def make_transaction(transaction_id, account_id=None, email=None, amount=100, timestamp="2026-01-01 10:00:00"):
	return frappe.get_doc(
		{
			"doctype": "CRM Transaction",
			"transaction_id": transaction_id,
			"account_id": account_id,
			"email": email,
			"timestamp": timestamp,
			"amount": amount,
		}
	).insert()


class TestClientTransactions(CRMTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		cls.client = make_client("TxnAlice", "txn-alice@example.com", "TXN-ACC-1")
		cls.other = make_client("TxnBob", "txn-bob@example.com", "TXN-ACC-2")
		make_transaction("TXN-T1", account_id="TXN-ACC-1")
		make_transaction("TXN-T2", email="txn-alice@example.com")
		make_transaction("TXN-T3", account_id="TXN-ACC-1", email="txn-alice@example.com")
		make_transaction("TXN-T4", account_id="TXN-ACC-2")
		make_transaction("TXN-T5", account_id="TXN-ACC-1", amount=-30)
		make_transaction("TXN-T6", email="txn-alice@example.com", amount=-20.5)

		cls.period_client = make_client("TxnPeriod", "txn-period@example.com", "TXN-ACC-P")
		now = now_datetime()
		make_transaction("TXN-P-TODAY", account_id="TXN-ACC-P", amount=100, timestamp=now)
		make_transaction("TXN-P-YEST", account_id="TXN-ACC-P", amount=-40, timestamp=add_days(now, -1))
		make_transaction("TXN-P-WEEK", account_id="TXN-ACC-P", amount=10, timestamp=add_days(now, -5))
		make_transaction("TXN-P-OLD", account_id="TXN-ACC-P", amount=1000, timestamp=add_days(now, -90))

	def ids(self, client):
		return {row.transaction_id for row in get_linked_transactions(client.name, period="all")["rows"]}

	def test_matches_on_account_id_or_email(self):
		self.assertEqual(self.ids(self.client), {"TXN-T1", "TXN-T2", "TXN-T3", "TXN-T5", "TXN-T6"})
		self.assertEqual(self.ids(self.other), {"TXN-T4"})

	def test_totals_split_deposits_from_withdrawals(self):
		# deposits 100 + 100 + 100, withdrawals 30 + 20.5
		result = get_linked_transactions(self.client.name, period="all")
		self.assertEqual(result["deposits"], 300)
		self.assertEqual(result["withdrawals"], 50.5)
		self.assertEqual(result["aum"], 249.5)

	def test_pages_cover_every_match_and_totals_ignore_the_page(self):
		first = get_linked_transactions(self.client.name, start=0, page_length=2, period="all")
		second = get_linked_transactions(self.client.name, start=2, page_length=2, period="all")
		third = get_linked_transactions(self.client.name, start=4, page_length=2, period="all")

		self.assertEqual(first["total_count"], 5)
		self.assertEqual([len(p["rows"]) for p in (first, second, third)], [2, 2, 1])
		ids = [row.transaction_id for p in (first, second, third) for row in p["rows"]]
		self.assertEqual(len(set(ids)), 5)
		# totals describe all 5 transactions whatever the page is
		self.assertEqual(first["deposits"], third["deposits"])
		self.assertEqual(first["aum"], 249.5)

	def period_ids(self, **kwargs):
		result = get_linked_transactions(self.period_client.name, **kwargs)
		return {row.transaction_id for row in result["rows"]}, result

	def test_defaults_to_today(self):
		ids, result = self.period_ids()
		self.assertEqual(ids, {"TXN-P-TODAY"})
		self.assertEqual((result["deposits"], result["withdrawals"], result["aum"]), (100, 0, 100))
		self.assertEqual((result["total_count"], result["overall_count"]), (1, 4))

	def test_yesterday_and_rolling_windows(self):
		self.assertEqual(self.period_ids(period="yesterday")[0], {"TXN-P-YEST"})
		self.assertEqual(
			self.period_ids(period="last_7_days")[0], {"TXN-P-TODAY", "TXN-P-YEST", "TXN-P-WEEK"}
		)
		self.assertNotIn("TXN-P-OLD", self.period_ids(period="last_30_days")[0])

	def test_all_time_has_every_transaction(self):
		ids, result = self.period_ids(period="all")
		self.assertEqual(len(ids), 4)
		self.assertEqual(result["aum"], 100 - 40 + 10 + 1000)

	def test_custom_range_is_inclusive_of_both_days(self):
		ids, result = self.period_ids(
			period="custom", date_from=add_days(nowdate(), -1), date_to=nowdate()
		)
		self.assertEqual(ids, {"TXN-P-TODAY", "TXN-P-YEST"})
		self.assertEqual((result["deposits"], result["withdrawals"]), (100, 40))

	def test_invalid_period_is_rejected(self):
		with self.assertRaises(frappe.ValidationError):
			get_linked_transactions(self.period_client.name, period="decade")

	def test_client_without_identifiers_has_no_transactions(self):
		client = make_client("TxnNoIds")
		self.assertEqual(
			get_linked_transactions(client.name, period="all"),
			{"rows": [], "total_count": 0, "overall_count": 0, "deposits": 0, "withdrawals": 0, "aum": 0},
		)

	def test_transaction_needs_account_id_or_email(self):
		with self.assertRaises(frappe.ValidationError):
			make_transaction("TXN-BAD")

	def test_transaction_id_is_unique(self):
		with self.assertRaises(frappe.DuplicateEntryError):
			make_transaction("TXN-T1", account_id="TXN-ACC-1")


class TestTransactionTotals(CRMTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_transaction("TOT-1", account_id="TOT-ACC-1", amount=100)
		make_transaction("TOT-2", account_id="TOT-ACC-1", amount=-30)
		make_transaction("TOT-3", account_id="TOT-ACC-2", amount=50)

	def test_totals_follow_the_list_filters(self):
		from crm.fcrm.doctype.crm_transaction.crm_transaction import get_totals

		mine = get_totals({"account_id": "TOT-ACC-1"})
		self.assertEqual(mine, {"deposits": 100, "withdrawals": 30, "aum": 70})

		# operator filters, as sent by the list's quick filters, and JSON strings both work
		like = get_totals('{"account_id": ["like", "TOT-ACC-%"]}')
		self.assertEqual((like["deposits"], like["withdrawals"], like["aum"]), (150, 30, 120))

		self.assertEqual(get_totals({"account_id": "TOT-NONE"}), {"deposits": 0, "withdrawals": 0, "aum": 0})

	def test_rejects_non_dict_filters(self):
		from crm.fcrm.doctype.crm_transaction.crm_transaction import get_totals

		with self.assertRaises(frappe.ValidationError):
			get_totals("[1, 2]")


class TestTimestampFilter(CRMTestCase):
	def test_today_is_one_whole_day(self):
		from crm.api.client import get_timestamp_filter

		today = nowdate()
		self.assertEqual(
			get_timestamp_filter("today"),
			{"timestamp": ["between", [f"{today} 00:00:00", f"{today} 23:59:59.999999"]]},
		)

	def test_all_time_is_unbounded(self):
		from crm.api.client import get_timestamp_filter

		self.assertEqual(get_timestamp_filter("all"), {})

	def test_custom_range_can_be_open_ended(self):
		from crm.api.client import get_timestamp_filter

		self.assertEqual(
			get_timestamp_filter("custom", date_from="2026-01-05"), {"timestamp": [">=", "2026-01-05 00:00:00"]}
		)
		self.assertEqual(
			get_timestamp_filter("custom", date_to="2026-01-09"),
			{"timestamp": ["<=", "2026-01-09 23:59:59.999999"]},
		)
