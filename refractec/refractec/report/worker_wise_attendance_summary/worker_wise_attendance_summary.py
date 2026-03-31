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
		{"fieldname": "worker", "label": "Worker ID", "fieldtype": "Link", "options": "Worker", "width": 140},
		{"fieldname": "worker_name", "label": "Worker Name", "fieldtype": "Data", "width": 180},
		{"fieldname": "worker_type", "label": "Type", "fieldtype": "Data", "width": 100},
		{"fieldname": "present_days", "label": "Present Days", "fieldtype": "Float", "width": 110},
		{"fieldname": "half_days", "label": "Half Days", "fieldtype": "Int", "width": 90},
		{"fieldname": "absent_days", "label": "Absent Days", "fieldtype": "Int", "width": 100},
		{"fieldname": "total_ot_hours", "label": "OT Hours", "fieldtype": "Float", "width": 100},
		{"fieldname": "gross_wage", "label": "Gross Wage", "fieldtype": "Currency", "width": 130},
		{"fieldname": "ot_amount", "label": "OT Amount", "fieldtype": "Currency", "width": 120},
		{"fieldname": "total_earning", "label": "Total Earning", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND da.project = %(project)s"
		values["project"] = filters["project"]

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND da.attendance_date BETWEEN %(from_date)s AND %(to_date)s"
		values["from_date"] = filters["from_date"]
		values["to_date"] = filters["to_date"]

	if filters.get("worker"):
		conditions += " AND ad.worker = %(worker)s"
		values["worker"] = filters["worker"]

	return frappe.db.sql(
		f"""
		SELECT
			ad.worker,
			ad.worker_name,
			ad.worker_type,
			SUM(CASE WHEN ad.status = 'Present' THEN 1 WHEN ad.status = 'Half Day' THEN 0.5 ELSE 0 END) as present_days,
			SUM(CASE WHEN ad.status = 'Half Day' THEN 1 ELSE 0 END) as half_days,
			SUM(CASE WHEN ad.status = 'Absent' THEN 1 ELSE 0 END) as absent_days,
			SUM(COALESCE(ad.overtime_hours, 0)) as total_ot_hours,
			SUM(COALESCE(ad.computed_wage, 0)) as gross_wage,
			SUM(COALESCE(ad.computed_ot_amount, 0)) as ot_amount,
			SUM(COALESCE(ad.total_for_day, 0)) as total_earning
		FROM `tabAttendance Detail` ad
		JOIN `tabDaily Attendance` da ON da.name = ad.parent
		WHERE da.docstatus = 1 {conditions}
		GROUP BY ad.worker, ad.worker_name, ad.worker_type
		ORDER BY ad.worker_name
	""",
		values,
		as_dict=True,
	)
