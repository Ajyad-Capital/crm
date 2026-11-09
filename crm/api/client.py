import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_first_day, getdate, nowdate

MAX_PAGE_LENGTH = 500

STATUSES = ("Approved", "Rejected", "Pending", "Blocked")

# Client check that is ticked once the client has a record of that doctype
ACTIVITY_FLAGS = {"funded": "CRM Transaction", "traded": "CRM Trade"}


def get_period_bounds(period: str, date_from=None, date_to=None):
	"""First day (inclusive) and day after the last (exclusive) of a period, in the site timezone.

	Either bound is None when the period is open on that side.
	"""
	today = getdate(nowdate())

	if period == "today":
		start, end = today, today
	elif period == "yesterday":
		start = end = add_days(today, -1)
	elif period == "last_7_days":
		start, end = add_days(today, -6), today
	elif period == "last_30_days":
		start, end = add_days(today, -29), today
	elif period == "this_month":
		start, end = get_first_day(today), today
	elif period == "custom":
		start = getdate(date_from) if date_from else None
		end = getdate(date_to) if date_to else None
	elif period == "all":
		start = end = None
	else:
		frappe.throw(_("Invalid period {0}").format(period))

	return start, add_days(end, 1) if end else None


def get_period_filters(period: str, date_from=None, date_to=None):
	"""Timestamp filters for a period; see get_period_bounds."""
	period_start, period_end = get_period_bounds(period, date_from, date_to)
	filters = []
	if period_start:
		filters.append(["timestamp", ">=", f"{period_start} 00:00:00"])
	if period_end:
		filters.append(["timestamp", "<", f"{period_end} 00:00:00"])
	return filters


def filters_to_conditions(filters):
	"""A list view filter dict ({field: value | [operator, value]}) as get_list filter conditions."""
	filters = frappe.parse_json(filters) or {}
	if not isinstance(filters, dict):
		frappe.throw(_("Invalid filters"))

	return [
		[fieldname, *value] if isinstance(value, list) else [fieldname, "=", value]
		for fieldname, value in filters.items()
	]


def build_link_filters(doc):
	"""OR filters matching records tied to a client by its Account ID or its Email."""
	or_filters = []
	if doc.get("account_id"):
		or_filters.append(["account_id", "=", doc.account_id])
	if doc.get("email"):
		or_filters.append(["email", "=", doc.email])
	return or_filters


def sync_funded_and_traded(doc):
	"""Tick Funded / Traded when transactions / trades already match this client.

	Covers clients created or edited after their records were imported. The other direction,
	a new record ticking its clients, is flag_linked_clients.
	"""
	or_filters = build_link_filters(doc)
	if not or_filters:
		return

	for fieldname, doctype in ACTIVITY_FLAGS.items():
		if not doc.get(fieldname) and frappe.get_all(doctype, or_filters=or_filters, limit=1, pluck="name"):
			doc.set(fieldname, 1)


def flag_linked_clients(doc, method=None):
	"""Tick Funded for the clients of a saved transaction, or Traded for those of a saved trade.

	Only ever ticks: removing or editing a record doesn't untick the client.
	"""
	fieldname = next(f for f, doctype in ACTIVITY_FLAGS.items() if doctype == doc.doctype)

	or_filters = []
	if doc.account_id:
		or_filters.append(["account_id", "=", doc.account_id])
	if doc.email:
		or_filters.append(["email", "=", doc.email])
	if not or_filters:
		return

	names = frappe.get_all("CRM Client", or_filters=or_filters, pluck="name")
	if names:
		frappe.db.set_value(
			"CRM Client", {"name": ["in", names], fieldname: 0}, fieldname, 1, update_modified=False
		)


def get_client_link_filters(client: str):
	return build_link_filters(frappe.get_doc("CRM Client", client))


def check_client_access(client: str):
	if not frappe.has_permission("CRM Client", "read", client):
		frappe.throw(_("Not permitted"), frappe.PermissionError)


@frappe.whitelist()
def get_status_counts(filters: str | dict | None = None):
	"""How many clients have each Status, among those matching the list view `filters`.

	A Status filter is ignored, so the counts of the other statuses stay visible while the list
	is narrowed to one. get_list applies the client permissions of the current user.
	"""
	conditions = [c for c in filters_to_conditions(filters) if c[0] != "status"]

	rows = frappe.get_list(
		"CRM Client",
		filters=conditions,
		fields=["status", {"COUNT": "*", "as": "count"}],
		group_by="status",
	)
	counts = {row.status: cint(row.count) for row in rows}

	return {status: counts.get(status, 0) for status in STATUSES}


@frappe.whitelist()
def get_timestamp_filter(period: str = "today", date_from: str | None = None, date_to: str | None = None):
	"""A list view `timestamp` filter for a period, in the site timezone ({} when it is unbounded)."""
	start, end = get_period_bounds(period, date_from, date_to)
	last_day = add_days(end, -1) if end else None
	first = f"{start} 00:00:00" if start else None
	last = f"{last_day} 23:59:59.999999" if last_day else None

	if first and last:
		return {"timestamp": ["between", [first, last]]}
	if first:
		return {"timestamp": [">=", first]}
	if last:
		return {"timestamp": ["<=", last]}
	return {}


@frappe.whitelist()
def get_linked_transactions(
	client: str,
	start: int = 0,
	page_length: int = 20,
	period: str = "today",
	date_from: str | None = None,
	date_to: str | None = None,
):
	"""A page of a client's transactions, matched on its Account ID or Email.

	Amounts are signed: a positive amount is a deposit and a negative one a withdrawal.
	`period` narrows the rows, `total_count` and the totals to a time window: today,
	yesterday, last_7_days, last_30_days, this_month, all, or custom (bounded by `date_from`
	and `date_to`). `overall_count` is the client's transactions across all time. Counts and totals are
	computed in the database, not from the returned page.
	"""

	empty = {"rows": [], "total_count": 0, "overall_count": 0, "deposits": 0, "withdrawals": 0, "aum": 0}

	check_client_access(client)

	start = max(cint(start), 0)
	page_length = min(max(cint(page_length), 1), MAX_PAGE_LENGTH)
	period_filters = get_period_filters(period, date_from, date_to)
	or_filters = get_client_link_filters(client)

	if not or_filters:
		return empty

	def aggregate(function, filters):
		# get_list applies the transaction permissions of the current user
		result = frappe.get_list(
			"CRM Transaction",
			or_filters=or_filters,
			filters=filters,
			fields=[{function: "amount" if function == "SUM" else "*", "as": "value"}],
		)
		return flt(result[0].value) if result else 0

	deposits = aggregate("SUM", [*period_filters, ["amount", ">", 0]])
	withdrawals = abs(aggregate("SUM", [*period_filters, ["amount", "<", 0]]))

	rows = frappe.get_list(
		"CRM Transaction",
		or_filters=or_filters,
		filters=period_filters,
		fields=["name", "transaction_id", "account_id", "email", "timestamp", "amount"],
		order_by="timestamp desc, name desc",
		offset=start,
		limit=page_length,
	)

	return {
		"rows": rows,
		"total_count": cint(aggregate("COUNT", period_filters)),
		"overall_count": cint(aggregate("COUNT", [])),
		"deposits": deposits,
		"withdrawals": withdrawals,
		"aum": deposits - withdrawals,
	}


@frappe.whitelist()
def get_linked_trades(
	client: str,
	start: int = 0,
	page_length: int = 20,
	period: str = "today",
	date_from: str | None = None,
	date_to: str | None = None,
):
	"""A page of a client's trades, matched on its Account ID or Email.

	`period` narrows the rows and `total_count` to a time window (see get_linked_transactions
	for the values). `overall_count` is the client's trades across all time. Counts are
	computed in the database, not from the returned page.
	"""

	empty = {"rows": [], "total_count": 0, "overall_count": 0}

	check_client_access(client)

	start = max(cint(start), 0)
	page_length = min(max(cint(page_length), 1), MAX_PAGE_LENGTH)
	period_filters = get_period_filters(period, date_from, date_to)
	or_filters = get_client_link_filters(client)

	if not or_filters:
		return empty

	def count(filters):
		# get_list applies the trade permissions of the current user
		result = frappe.get_list(
			"CRM Trade",
			or_filters=or_filters,
			filters=filters,
			fields=[{"COUNT": "*", "as": "value"}],
		)
		return cint(result[0].value) if result else 0

	rows = frappe.get_list(
		"CRM Trade",
		or_filters=or_filters,
		filters=period_filters,
		fields=[
			"name",
			"account_id",
			"email",
			"symbol_id",
			"symbol",
			"quantity",
			"price",
			"currency",
			"side",
			"commission",
			"timestamp",
		],
		order_by="timestamp desc, name desc",
		offset=start,
		limit=page_length,
	)

	return {"rows": rows, "total_count": count(period_filters), "overall_count": count([])}
