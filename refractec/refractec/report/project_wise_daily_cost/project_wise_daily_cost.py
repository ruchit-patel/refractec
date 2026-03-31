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
		{"fieldname": "attendance_date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "labor_cost", "label": "Labor Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "expense_cost", "label": "Expense Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_cost", "label": "Total Cost", "fieldtype": "Currency", "width": 130},
		{"fieldname": "workers_present", "label": "Workers Present", "fieldtype": "Int", "width": 120},
		{"fieldname": "overtime_hours", "label": "OT Hours", "fieldtype": "Float", "width": 100},
	]


def get_data(filters):
	if not filters.get("project"):
		frappe.throw("Please select a Project")

	conditions = "AND da.attendance_date BETWEEN %(from_date)s AND %(to_date)s" if filters.get("from_date") and filters.get("to_date") else ""

	labor_data = frappe.db.sql(
		f"""
		SELECT
			da.attendance_date,
			SUM(ad.total_for_day) as labor_cost,
			SUM(CASE WHEN ad.status IN ('Present', 'Half Day') THEN 1 ELSE 0 END) as workers_present,
			SUM(COALESCE(ad.overtime_hours, 0)) as overtime_hours
		FROM `tabDaily Attendance` da
		JOIN `tabAttendance Detail` ad ON ad.parent = da.name
		WHERE da.project = %(project)s AND da.docstatus = 1 {conditions}
		GROUP BY da.attendance_date
		ORDER BY da.attendance_date
	""",
		filters,
		as_dict=True,
	)

	expense_data = {}
	expenses = frappe.db.sql(
		f"""
		SELECT
			expense_date,
			SUM(amount) as expense_cost
		FROM `tabExpense Entry`
		WHERE project = %(project)s AND docstatus = 1
			AND approval_status IN ('Auto Approved', 'Manually Approved')
			{"AND expense_date BETWEEN %(from_date)s AND %(to_date)s" if filters.get("from_date") and filters.get("to_date") else ""}
		GROUP BY expense_date
	""",
		filters,
		as_dict=True,
	)
	for e in expenses:
		expense_data[str(e.expense_date)] = flt(e.expense_cost)

	data = []
	for row in labor_data:
		date_str = str(row.attendance_date)
		exp_cost = expense_data.get(date_str, 0)
		data.append({
			"attendance_date": row.attendance_date,
			"labor_cost": flt(row.labor_cost),
			"expense_cost": exp_cost,
			"total_cost": flt(row.labor_cost) + exp_cost,
			"workers_present": row.workers_present,
			"overtime_hours": flt(row.overtime_hours),
		})

	return data


def get_chart(data):
	if not data:
		return None
	return {
		"data": {
			"labels": [str(d["attendance_date"]) for d in data],
			"datasets": [
				{"name": "Labor Cost", "values": [flt(d["labor_cost"]) for d in data]},
				{"name": "Expense Cost", "values": [flt(d["expense_cost"]) for d in data]},
			],
		},
		"type": "line",
	}
