import json

import frappe

QUICK_FILTERS = {
	"CRM Transaction": ["account_id", "email"],
	"CRM Trade": ["account_id", "email", "symbol_id", "side"],
}


def execute():
	for dt, filters in QUICK_FILTERS.items():
		name = frappe.db.get_value("CRM Global Settings", {"dt": dt})
		if name:
			frappe.db.set_value("CRM Global Settings", name, "json", json.dumps(filters))
			continue

		frappe.get_doc({"doctype": "CRM Global Settings", "dt": dt, "json": json.dumps(filters)}).insert(
			ignore_permissions=True
		)
