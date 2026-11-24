import json

import frappe

DOCTYPE = "CRM Transaction"
REMOVED = {"email"}
RENAMED = {"transaction_id": "name"}


def execute():
	"""Bring the saved views and quick filters of CRM Transaction in line with its fields.

	Email is gone and the record ID (`name`) replaced the separate Transaction ID field.
	"""
	for name in frappe.get_all("CRM View Settings", filters={"dt": DOCTYPE}, pluck="name"):
		doc = frappe.get_doc("CRM View Settings", name)
		doc.columns = dump(update_columns(load(doc.columns)))
		doc.rows = dump(update_names(load(doc.rows)))
		doc.filters = dump(update_filters(load(doc.filters)))
		doc.save(ignore_permissions=True)

	name = frappe.db.get_value("CRM Global Settings", {"dt": DOCTYPE})
	if name:
		quick_filters = update_names(load(frappe.db.get_value("CRM Global Settings", name, "json")))
		frappe.db.set_value("CRM Global Settings", name, "json", dump(quick_filters))


def load(value):
	try:
		return json.loads(value) if value else None
	except ValueError:
		return None


def dump(value):
	return json.dumps(value) if value is not None else None


def update_names(fieldnames):
	if fieldnames is None:
		return None

	result = []
	for fieldname in fieldnames:
		fieldname = RENAMED.get(fieldname, fieldname)
		if fieldname not in REMOVED and fieldname not in result:
			result.append(fieldname)
	return result


def update_columns(columns):
	if columns is None:
		return None

	result = []
	for column in columns:
		if column.get("key") in RENAMED:
			column = {**column, "key": RENAMED[column["key"]], "label": "ID"}
		if column.get("key") not in REMOVED and column.get("key") not in [c.get("key") for c in result]:
			result.append(column)
	return result


def update_filters(filters):
	if filters is None:
		return None
	return {RENAMED.get(k, k): v for k, v in filters.items() if k not in REMOVED}
