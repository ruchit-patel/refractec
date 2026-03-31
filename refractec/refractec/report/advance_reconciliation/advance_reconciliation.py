# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "posting_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "transaction_type", "label": "Type", "fieldtype": "Data", "width": 140},
		{"fieldname": "amount", "label": "Amount", "fieldtype": "Currency", "width": 120},
		{"fieldname": "running_balance", "label": "Balance", "fieldtype": "Currency", "width": 120},
		{"fieldname": "reference_doctype", "label": "Ref DocType", "fieldtype": "Data", "width": 130},
		{"fieldname": "reference_name", "label": "Ref Name", "fieldtype": "Dynamic Link", "options": "reference_doctype", "width": 150},
		{"fieldname": "remarks", "label": "Remarks", "fieldtype": "Data", "width": 250},
		{"fieldname": "worker", "label": "Worker", "fieldtype": "Link", "options": "Worker", "width": 130},
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 130},
	]


def get_data(filters):
	if not filters.get("worker") and not filters.get("project"):
		frappe.throw("Please select at least a Worker or Project")

	conditions = ""
	values = {}

	if filters.get("worker"):
		conditions += " AND worker = %(worker)s"
		values["worker"] = filters["worker"]

	if filters.get("project"):
		conditions += " AND project = %(project)s"
		values["project"] = filters["project"]

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND posting_date BETWEEN %(from_date)s AND %(to_date)s"
		values["from_date"] = filters["from_date"]
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		f"""
		SELECT
			posting_date, transaction_type, amount, running_balance,
			reference_doctype, reference_name, remarks, worker, project
		FROM `tabAdvance Ledger Entry`
		WHERE 1=1 {conditions}
		ORDER BY posting_date ASC, creation ASC
	""",
		values,
		as_dict=True,
	)
