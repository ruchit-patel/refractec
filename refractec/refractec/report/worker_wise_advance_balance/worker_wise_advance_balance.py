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
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "total_given", "label": "Total Given", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_recovered", "label": "Total Recovered", "fieldtype": "Currency", "width": 130},
		{"fieldname": "outstanding", "label": "Outstanding", "fieldtype": "Currency", "width": 130},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND wa.project = %(project)s"
		values["project"] = filters["project"]

	if filters.get("worker"):
		conditions += " AND wa.worker = %(worker)s"
		values["worker"] = filters["worker"]

	return frappe.db.sql(
		f"""
		SELECT
			wa.worker,
			w.worker_name,
			wa.project,
			SUM(wa.amount) as total_given,
			SUM(COALESCE(wa.recovered_amount, 0)) as total_recovered,
			SUM(wa.amount - COALESCE(wa.recovered_amount, 0)) as outstanding
		FROM `tabWorker Advance` wa
		JOIN `tabWorker` w ON w.name = wa.worker
		WHERE wa.docstatus = 1 {conditions}
		GROUP BY wa.worker, w.worker_name, wa.project
		HAVING outstanding > 0
		ORDER BY outstanding DESC
	""",
		values,
		as_dict=True,
	)
