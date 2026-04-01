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
		{
			"label": "Employee Name",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Worker ID",
			"fieldname": "worker",
			"fieldtype": "Link",
			"options": "Worker",
			"width": 140,
		},
		{
			"label": "Designation",
			"fieldname": "worker_type",
			"fieldtype": "Data",
			"width": 100,
		},
		{
			"label": "Project",
			"fieldname": "project",
			"fieldtype": "Link",
			"options": "Project",
			"width": 140,
		},
		{
			"label": "Bank Name",
			"fieldname": "bank_name",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Account No",
			"fieldname": "bank_account_no",
			"fieldtype": "Data",
			"width": 160,
		},
		{
			"label": "IFSC Code",
			"fieldname": "ifsc_code",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": "Gross Pay",
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"width": 120,
		},
		{
			"label": "Total Deductions",
			"fieldname": "total_all_deductions",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": "Net Pay",
			"fieldname": "net_pay",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": "Narration",
			"fieldname": "narration",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": "Salary Slip",
			"fieldname": "salary_slip",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": "Payroll Entry",
			"fieldname": "payroll_entry",
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"width": 150,
		},
	]


def get_data(filters):
	conditions = {
		"payroll_month": filters.get("payroll_month"),
		"payroll_year": filters.get("payroll_year"),
	}
	if filters.get("project"):
		conditions["project"] = filters.get("project")

	slips = frappe.get_all(
		"Salary Slip",
		filters=conditions,
		fields=[
			"name", "employee_name", "worker", "worker_name", "worker_type",
			"project", "gross_pay", "total_all_deductions", "net_pay",
			"payroll_entry", "payroll_month", "payroll_year",
		],
		order_by="employee_name asc",
	)

	# Fetch bank details for workers in one query
	worker_ids = [s.worker for s in slips if s.worker]
	bank_details = {}
	if worker_ids:
		workers = frappe.get_all(
			"Worker",
			filters={"name": ["in", worker_ids]},
			fields=["name", "bank_name", "bank_account_no", "ifsc_code"],
		)
		for w in workers:
			bank_details[w.name] = w

	data = []
	for s in slips:
		bank = bank_details.get(s.worker, {})
		narration = f"Salary {s.payroll_month} {s.payroll_year}"
		if s.project:
			narration += f" - {s.project}"

		data.append({
			"employee_name": s.employee_name or s.worker_name,
			"worker": s.worker,
			"worker_type": s.worker_type,
			"project": s.project,
			"bank_name": bank.get("bank_name", ""),
			"bank_account_no": bank.get("bank_account_no", ""),
			"ifsc_code": bank.get("ifsc_code", ""),
			"gross_pay": flt(s.gross_pay),
			"total_all_deductions": flt(s.total_all_deductions),
			"net_pay": flt(s.net_pay),
			"narration": narration,
			"salary_slip": s.name,
			"payroll_entry": s.payroll_entry,
		})

	return data
