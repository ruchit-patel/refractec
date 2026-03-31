# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": "Payroll Entry", "fieldtype": "Link", "options": "Payroll Entry", "width": 150},
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "payroll_month", "label": "Month", "fieldtype": "Data", "width": 100},
		{"fieldname": "payroll_year", "label": "Year", "fieldtype": "Int", "width": 70},
		{"fieldname": "worker_count", "label": "Workers", "fieldtype": "Int", "width": 80},
		{"fieldname": "total_gross_pay", "label": "Gross Pay", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_advance_deduction", "label": "Advance Deduction", "fieldtype": "Currency", "width": 140},
		{"fieldname": "total_net_pay", "label": "Net Pay", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND pe.project = %(project)s"
		values["project"] = filters["project"]

	if filters.get("payroll_year"):
		conditions += " AND pe.payroll_year = %(payroll_year)s"
		values["payroll_year"] = filters["payroll_year"]

	return frappe.db.sql(
		f"""
		SELECT
			pe.name,
			pe.project,
			pe.payroll_month,
			pe.payroll_year,
			(SELECT COUNT(*) FROM `tabPayroll Detail` pd WHERE pd.parent = pe.name) as worker_count,
			pe.total_gross_pay,
			pe.total_advance_deduction,
			pe.total_net_pay
		FROM `tabPayroll Entry` pe
		WHERE pe.docstatus = 1 {conditions}
		ORDER BY pe.payroll_year DESC, FIELD(pe.payroll_month,
			'January','February','March','April','May','June',
			'July','August','September','October','November','December') DESC
	""",
		values,
		as_dict=True,
	)
