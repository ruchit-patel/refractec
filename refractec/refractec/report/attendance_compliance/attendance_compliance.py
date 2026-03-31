# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate, add_days, today


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "project_name", "label": "Project Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "date", "label": "Date", "fieldtype": "Date", "width": 110},
		{"fieldname": "status", "label": "Status", "fieldtype": "Data", "width": 120},
	]


def get_data(filters):
	num_days = filters.get("num_days", 7) if filters else 7
	current_date = getdate(today())

	active_projects = frappe.get_all(
		"Project",
		filters={"status": "In Progress"},
		fields=["name", "project_name"],
	)

	existing_attendance = {}
	attendance_records = frappe.get_all(
		"Daily Attendance",
		filters={
			"docstatus": ["!=", 2],
			"attendance_date": [">=", add_days(current_date, -num_days)],
		},
		fields=["project", "attendance_date"],
	)
	for rec in attendance_records:
		key = f"{rec.project}|{rec.attendance_date}"
		existing_attendance[key] = True

	data = []
	for project in active_projects:
		for i in range(num_days):
			check_date = add_days(current_date, -i)
			key = f"{project.name}|{check_date}"
			has_attendance = key in existing_attendance

			if not has_attendance:
				data.append({
					"project": project.name,
					"project_name": project.project_name,
					"date": check_date,
					"status": "Missing",
				})

	data.sort(key=lambda x: (x["date"], x["project_name"]), reverse=True)
	return data
