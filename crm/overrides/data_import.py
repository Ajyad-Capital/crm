import re

from frappe.core.doctype.data_import import importer
from frappe.core.doctype.data_import.data_import import DataImport

from crm.utils.timezones import to_site_time

# 2026-11-20T15:23:38.500Z, 2026-11-20T18:23:38+03:00
ISO_TIMESTAMP_WITH_ZONE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})$")


def read_iso_timestamps(get_datetime):
	"""Make the importer accept ISO 8601 timestamps that carry a timezone.

	Frappe only reads datetimes in the formats it can guess, which do not include these, so such
	a value is reported as not a valid datetime. It is converted to site time instead.
	"""

	def wrapper(self, value, column):
		if isinstance(value, str) and ISO_TIMESTAMP_WITH_ZONE.match(value.strip()):
			converted = to_site_time(value.strip())
			if not isinstance(converted, str):
				return converted
		return get_datetime(self, value, column)

	wrapper.reads_iso_timestamps = True
	return wrapper


if not getattr(importer.Row.get_datetime, "reads_iso_timestamps", False):
	importer.Row.get_datetime = read_iso_timestamps(importer.Row.get_datetime)


class DataImportListView:
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "ID",
				"type": "Data",
				"key": "name",
				"width": "16rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "10rem",
			},
			{
				"label": "Document Type",
				"type": "Link",
				"key": "reference_doctype",
				"width": "12rem",
			},
			{
				"label": "Import Type",
				"type": "Select",
				"key": "import_type",
				"width": "12rem",
			},
			{
				"label": "Import File",
				"type": "Attach",
				"key": "import_file",
				"width": "16rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"status",
			"reference_doctype",
			"import_type",
			"import_file",
			"google_sheets_url",
			"modified",
		]
		return {"columns": columns, "rows": rows}


class DataImportV15(DataImportListView, DataImport):
	pass
