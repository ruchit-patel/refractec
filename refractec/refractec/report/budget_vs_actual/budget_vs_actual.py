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
		{"fieldname": "project", "label": "Project", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "project_name", "label": "Project Name", "fieldtype": "Data", "width": 180},
		{"fieldname": "budget_head", "label": "Budget Head", "fieldtype": "Data", "width": 150},
		{"fieldname": "allocated_amount", "label": "Allocated", "fieldtype": "Currency", "width": 130},
		{"fieldname": "spent_amount", "label": "Spent", "fieldtype": "Currency", "width": 130},
		{"fieldname": "remaining_amount", "label": "Remaining", "fieldtype": "Currency", "width": 130},
		{"fieldname": "utilization_pct", "label": "Utilization %", "fieldtype": "Percent", "width": 110},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND p.name = %(project)s"
		values["project"] = filters["project"]

	if filters.get("status"):
		conditions += " AND p.status = %(status)s"
		values["status"] = filters["status"]

	data = frappe.db.sql(
		f"""
		SELECT
			p.name as project,
			p.project_name,
			pbi.budget_head,
			pbi.allocated_amount,
			COALESCE(pbi.spent_amount, 0) as spent_amount,
			COALESCE(pbi.remaining_amount, pbi.allocated_amount) as remaining_amount
		FROM `tabProject Budget Item` pbi
		JOIN `tabProject` p ON p.name = pbi.parent
		WHERE 1=1 {conditions}
		ORDER BY p.name, pbi.idx
	""",
		values,
		as_dict=True,
	)

	for row in data:
		if flt(row.allocated_amount):
			row["utilization_pct"] = (flt(row.spent_amount) / flt(row.allocated_amount)) * 100
		else:
			row["utilization_pct"] = 0

	return data


def get_chart(data):
	if not data:
		return None

	labels = [f"{d.project_name} - {d.budget_head}" for d in data[:15]]
	allocated = [flt(d.allocated_amount) for d in data[:15]]
	spent = [flt(d.spent_amount) for d in data[:15]]

	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": "Allocated", "values": allocated},
				{"name": "Spent", "values": spent},
			],
		},
		"type": "bar",
	}
