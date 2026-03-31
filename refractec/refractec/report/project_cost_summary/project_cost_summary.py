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
		{"fieldname": "name", "label": "Project ID", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "project_name", "label": "Project Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 100},
		{"fieldname": "project_budget", "label": "Budget", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_labor_cost", "label": "Labor Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_expense_cost", "label": "Expense Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_cost", "label": "Total Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "budget_variance", "label": "Variance", "fieldtype": "Currency", "width": 130},
		{"fieldname": "budget_utilization_pct", "label": "Utilization %", "fieldtype": "Percent", "width": 110},
		{"fieldname": "total_advance_given", "label": "Advances Given", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_advance_recovered", "label": "Advances Recovered", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("status"):
		conditions += " AND status = %(status)s"
		values["status"] = filters["status"]

	if filters.get("from_date"):
		conditions += " AND start_date >= %(from_date)s"
		values["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions += " AND start_date <= %(to_date)s"
		values["to_date"] = filters["to_date"]

	return frappe.db.sql(
		f"""
		SELECT
			name, project_name, status, project_budget,
			COALESCE(total_labor_cost, 0) as total_labor_cost,
			COALESCE(total_expense_cost, 0) as total_expense_cost,
			COALESCE(total_cost, 0) as total_cost,
			COALESCE(budget_variance, 0) as budget_variance,
			COALESCE(budget_utilization_pct, 0) as budget_utilization_pct,
			COALESCE(total_advance_given, 0) as total_advance_given,
			COALESCE(total_advance_recovered, 0) as total_advance_recovered
		FROM `tabProject`
		WHERE 1=1 {conditions}
		ORDER BY total_cost DESC
	""",
		values,
		as_dict=True,
	)


def get_chart(data):
	if not data:
		return None

	labels = [d.project_name for d in data[:10]]
	budget = [flt(d.project_budget) for d in data[:10]]
	actual = [flt(d.total_cost) for d in data[:10]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Budget", "values": budget},
				{"name": "Actual Cost", "values": actual},
			],
		},
		"type": "bar",
	}
