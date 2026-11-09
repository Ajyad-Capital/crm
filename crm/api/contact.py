import frappe
from frappe import _
from frappe.utils import add_days, cint, flt, get_first_day, getdate, nowdate


def validate(doc, method):
	validate_unique_identifiers(doc)
	update_deals_email_mobile_no(doc)


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


MAX_TRANSACTIONS_PAGE_LENGTH = 500


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
	period_start, period_end = get_period_bounds(period, date_from, date_to)

	doc = frappe.get_doc("Contact", contact)
	or_filters = []
	if doc.get("ajyad_account_id"):
		or_filters.append(["account_id", "=", doc.ajyad_account_id])
	emails = [row.email_id for row in doc.email_ids if row.email_id]
	if emails:
		or_filters.append(["email", "in", emails])

	if not or_filters:
		return empty

	period_filters = []
	if period_start:
		period_filters.append(["timestamp", ">=", f"{period_start} 00:00:00"])
	if period_end:
		period_filters.append(["timestamp", "<", f"{period_end} 00:00:00"])

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
