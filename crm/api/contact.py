import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_first_day, getdate, nowdate


def validate(doc, method):
	validate_unique_identifiers(doc)
	update_deals_email_mobile_no(doc)
	sync_funded_and_traded(doc)


# Contact check that is ticked once the contact has a record of that doctype
ACTIVITY_FLAGS = {"ajyad_funded": "CRM Transaction", "ajyad_traded": "CRM Trade"}


def sync_funded_and_traded(doc):
	"""Tick Funded / Traded when transactions / trades already match this contact.

	Covers contacts created or edited after their records were imported. The other direction,
	a new record ticking its contacts, is flag_linked_contacts.
	"""
	or_filters = build_link_filters(doc)
	if not or_filters:
		return

	for fieldname, doctype in ACTIVITY_FLAGS.items():
		if not doc.get(fieldname) and frappe.get_all(doctype, or_filters=or_filters, limit=1, pluck="name"):
			doc.set(fieldname, 1)


def flag_linked_contacts(doc, method=None):
	"""Tick Funded for the contacts of a saved transaction, or Traded for those of a saved trade.

	Only ever ticks: removing or editing a record doesn't untick the contact.
	"""
	fieldname = next(f for f, doctype in ACTIVITY_FLAGS.items() if doctype == doc.doctype)

	names = set()
	if doc.account_id:
		names.update(frappe.get_all("Contact", filters={"ajyad_account_id": doc.account_id}, pluck="name"))
	if doc.email:
		names.update(
			frappe.get_all(
				"Contact Email", filters={"email_id": doc.email, "parenttype": "Contact"}, pluck="parent"
			)
		)

	if names:
		frappe.db.set_value(
			"Contact", {"name": ["in", list(names)], fieldname: 0}, fieldname, 1, update_modified=False
		)


def validate_unique_identifiers(doc):
	"""Email and Account ID identify a contact, so neither can be shared between contacts.

	Only checked when the value is new or changed, so existing duplicates don't block
	unrelated edits to those contacts.
	"""
	for fieldname, label in (("email_id", _("Email")), ("ajyad_account_id", _("Account ID"))):
		value = doc.get(fieldname)
		if not value or not (doc.is_new() or doc.has_value_changed(fieldname)):
			continue

		duplicate = frappe.db.exists("Contact", {fieldname: value, "name": ["!=", doc.name]})
		if duplicate:
			frappe.throw(
				_("{0} {1} is already used by contact {2}").format(label, value, duplicate),
				frappe.DuplicateEntryError,
			)


def update_deals_email_mobile_no(doc):
	linked_deals = frappe.get_all(
		"CRM Contacts",
		filters={"contact": doc.name, "is_primary": 1},
		fields=["parent"],
	)

	for linked_deal in linked_deals:
		deal = frappe.db.get_values("CRM Deal", linked_deal.parent, ["email", "mobile_no"], as_dict=True)[0]
		if deal.email != doc.email_id or deal.mobile_no != doc.mobile_no:
			frappe.db.set_value(
				"CRM Deal",
				linked_deal.parent,
				{
					"email": doc.email_id,
					"mobile_no": doc.mobile_no,
				},
			)


MAX_TRANSACTIONS_PAGE_LENGTH = 500  # also caps trade pages


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


def filters_to_conditions(filters):
	"""A list view filter dict ({field: value | [operator, value]}) as get_list filter conditions."""
	filters = frappe.parse_json(filters) or {}
	if not isinstance(filters, dict):
		frappe.throw(_("Invalid filters"))

	return [
		[fieldname, *value] if isinstance(value, list) else [fieldname, "=", value]
		for fieldname, value in filters.items()
	]


@frappe.whitelist()
def get_status_counts(filters: str | dict | None = None):
	"""How many contacts have each Status, among those matching the list view `filters`.

	A Status filter is ignored, so the counts of the other statuses stay visible while the list
	is narrowed to one. get_list applies the contact permissions of the current user.
	"""
	conditions = [c for c in filters_to_conditions(filters) if c[0] != "ajyad_status"]

	rows = frappe.get_list(
		"Contact",
		filters=conditions,
		fields=["ajyad_status", {"COUNT": "*", "as": "count"}],
		group_by="ajyad_status",
	)
	counts = {row.ajyad_status: cint(row.count) for row in rows}

	return {status: counts.get(status, 0) for status in ("Approved", "Rejected", "Pending", "Blocked")}


def get_contact_link_filters(contact: str):
	"""OR filters matching records tied to a contact by its Account ID or any of its emails."""
	return build_link_filters(frappe.get_doc("Contact", contact))


def build_link_filters(doc):
	or_filters = []
	if doc.get("ajyad_account_id"):
		or_filters.append(["account_id", "=", doc.ajyad_account_id])
	emails = [row.email_id for row in doc.email_ids if row.email_id]
	if emails:
		or_filters.append(["email", "in", emails])
	return or_filters


def get_period_filters(period: str, date_from=None, date_to=None):
	"""Timestamp filters for a period; see get_period_bounds."""
	period_start, period_end = get_period_bounds(period, date_from, date_to)
	filters = []
	if period_start:
		filters.append(["timestamp", ">=", f"{period_start} 00:00:00"])
	if period_end:
		filters.append(["timestamp", "<", f"{period_end} 00:00:00"])
	return filters


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
	contact: str,
	start: int = 0,
	page_length: int = 20,
	period: str = "today",
	date_from: str | None = None,
	date_to: str | None = None,
):
	"""A page of a contact's transactions, matched on its Account ID or any of its emails.

	Amounts are signed: a positive amount is a deposit and a negative one a withdrawal.
	`period` narrows the rows, `total_count` and the totals to a time window: today,
	yesterday, last_7_days, last_30_days, this_month, all, or custom (bounded by `date_from`
	and `date_to`). `overall_count` is the contact's transactions across all time. Counts and totals are computed in the
	database, not from the returned page.
	"""

	empty = {"rows": [], "total_count": 0, "overall_count": 0, "deposits": 0, "withdrawals": 0, "aum": 0}

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	start = max(cint(start), 0)
	page_length = min(max(cint(page_length), 1), MAX_TRANSACTIONS_PAGE_LENGTH)
	period_filters = get_period_filters(period, date_from, date_to)
	or_filters = get_contact_link_filters(contact)

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
	contact: str,
	start: int = 0,
	page_length: int = 20,
	period: str = "today",
	date_from: str | None = None,
	date_to: str | None = None,
):
	"""A page of a contact's trades, matched on its Account ID or any of its emails.

	`period` narrows the rows and `total_count` to a time window (see get_linked_transactions
	for the values). `overall_count` is the contact's trades across all time. Counts are
	computed in the database, not from the returned page.
	"""

	empty = {"rows": [], "total_count": 0, "overall_count": 0}

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	start = max(cint(start), 0)
	page_length = min(max(cint(page_length), 1), MAX_TRANSACTIONS_PAGE_LENGTH)
	period_filters = get_period_filters(period, date_from, date_to)
	or_filters = get_contact_link_filters(contact)

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


@frappe.whitelist()
def get_linked_deals(contact: str):
	"""Get linked deals for a contact"""

	if not frappe.has_permission("Contact", "read", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	deal_names = frappe.get_all(
		"CRM Contacts",
		filters={"contact": contact, "parenttype": "CRM Deal"},
		fields=["parent"],
		distinct=True,
	)

	# get deals data
	deals = []
	for d in deal_names:
		deal = frappe.get_cached_doc(
			"CRM Deal",
			d.parent,
			fields=[
				"name",
				"organization",
				"currency",
				"deal_value",
				"status",
				"email",
				"mobile_no",
				"deal_owner",
				"modified",
			],
		)
		deals.append(deal.as_dict())

	return deals


@frappe.whitelist()
def create_new(contact: str, field: str, value: str):
	"""Create new email or phone for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_cached_doc("Contact", contact)

	if field == "email":
		email = {"email_id": value, "is_primary": 1 if len(contact.email_ids) == 0 else 0}
		contact.append("email_ids", email)
	elif field in ("mobile_no", "phone"):
		mobile_no = {"phone": value, "is_primary_mobile_no": 1 if len(contact.phone_nos) == 0 else 0}
		contact.append("phone_nos", mobile_no)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def set_as_primary(contact: str, field: str, value: str):
	"""Set email or phone as primary for a contact"""
	if not frappe.has_permission("Contact", "write", contact):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	contact = frappe.get_doc("Contact", contact)

	if field == "email":
		for email in contact.email_ids:
			if email.email_id == value:
				email.is_primary = 1
			else:
				email.is_primary = 0
	elif field in ("mobile_no", "phone"):
		name = "is_primary_mobile_no" if field == "mobile_no" else "is_primary_phone"
		for phone in contact.phone_nos:
			if phone.phone == value:
				phone.set(name, 1)
			else:
				phone.set(name, 0)
	else:
		frappe.throw(_("Invalid field"))

	contact.save()
	return True


@frappe.whitelist()
def search_emails(txt: str):
	doctype = "Contact"
	meta = frappe.get_meta(doctype)
	filters = [["Contact", "email_id", "is", "set"]]

	if meta.get("fields", {"fieldname": "enabled", "fieldtype": "Check"}):
		filters.append([doctype, "enabled", "=", 1])
	if meta.get("fields", {"fieldname": "disabled", "fieldtype": "Check"}):
		filters.append([doctype, "disabled", "!=", 1])

	or_filters = []
	search_fields = ["full_name", "email_id", "name"]
	if txt:
		for f in search_fields:
			or_filters.append([doctype, f.strip(), "like", f"%{txt}%"])

	results = frappe.get_list(
		doctype,
		filters=filters,
		fields=search_fields,
		or_filters=or_filters,
		limit_start=0,
		limit_page_length=20,
		order_by="email_id, full_name, name",
		ignore_permissions=False,
		as_list=True,
		strict=False,
	)

	return results
