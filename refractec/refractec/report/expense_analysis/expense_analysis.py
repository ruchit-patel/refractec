# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns():
	return [
		{"fieldname": "expense_type", "label": "Expense Type", "fieldtype": "Link", "options": "Expense Type", "width": 150},
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "total_amount", "label": "Total Amount", "fieldtype": "Currency", "width": 130},
		{"fieldname": "auto_approved_count", "label": "Auto Approved", "fieldtype": "Int", "width": 110},
		{"fieldname": "manually_approved_count", "label": "Manually Approved", "fieldtype": "Int", "width": 130},
		{"fieldname": "pending_count", "label": "Pending", "fieldtype": "Int", "width": 90},
		{"fieldname": "rejected_count", "label": "Rejected", "fieldtype": "Int", "width": 90},
		{"fieldname": "total_entries", "label": "Total Entries", "fieldtype": "Int", "width": 110},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND project = %(project)s"
		values["project"] = filters["project"]

	if filters.get("expense_type"):
		conditions += " AND expense_type = %(expense_type)s"
		values["expense_type"] = filters["expense_type"]

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND expense_date BETWEEN %(from_date)s AND %(to_date)s"
		values["from_date"] = filters["from_date"]
		values["to_date"] = filters["to_date"]

	if filters.get("approval_status"):
		conditions += " AND approval_status = %(approval_status)s"
		values["approval_status"] = filters["approval_status"]

	return frappe.db.sql(
		f"""
		SELECT
			expense_type,
			project,
			SUM(amount) as total_amount,
			SUM(CASE WHEN approval_status = 'Auto Approved' THEN 1 ELSE 0 END) as auto_approved_count,
			SUM(CASE WHEN approval_status = 'Manually Approved' THEN 1 ELSE 0 END) as manually_approved_count,
			SUM(CASE WHEN approval_status = 'Pending Approval' THEN 1 ELSE 0 END) as pending_count,
			SUM(CASE WHEN approval_status = 'Rejected' THEN 1 ELSE 0 END) as rejected_count,
			COUNT(*) as total_entries
		FROM `tabExpense Entry`
		WHERE docstatus = 1 {conditions}
		GROUP BY expense_type, project
		ORDER BY total_amount DESC
	""",
		values,
		as_dict=True,
	)


def get_chart(data):
	if not data:
		return None

	type_totals = {}
	for row in data:
		et = row.expense_type
		type_totals[et] = flt(type_totals.get(et, 0)) + flt(row.total_amount)

	sorted_types = sorted(type_totals.items(), key=lambda x: x[1], reverse=True)[:10]

	return {
		"data": {
			"labels": [t[0] for t in sorted_types],
			"datasets": [{"name": "Amount", "values": [t[1] for t in sorted_types]}],
		},
		"type": "pie",
	}
