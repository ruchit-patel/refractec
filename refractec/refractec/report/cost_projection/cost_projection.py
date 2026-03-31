# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate, date_diff, add_days, today


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"fieldname": "name", "label": "Project ID", "fieldtype": "Link", "options": "Project", "width": 140},
		{"fieldname": "project_name", "label": "Project Name", "fieldtype": "Data", "width": 200},
		{"fieldname": "project_budget", "label": "Budget", "fieldtype": "Currency", "width": 130},
		{"fieldname": "total_cost", "label": "Cost to Date", "fieldtype": "Currency", "width": 130},
		{"fieldname": "days_elapsed", "label": "Days Elapsed", "fieldtype": "Int", "width": 100},
		{"fieldname": "daily_burn_rate", "label": "Daily Burn Rate", "fieldtype": "Currency", "width": 130},
		{"fieldname": "days_remaining", "label": "Days to End", "fieldtype": "Int", "width": 100},
		{"fieldname": "projected_total_cost", "label": "Projected Total", "fieldtype": "Currency", "width": 130},
		{"fieldname": "projected_overrun", "label": "Projected Overrun", "fieldtype": "Currency", "width": 130},
		{"fieldname": "budget_exhaustion_date", "label": "Budget Exhaustion Date", "fieldtype": "Date", "width": 140},
	]


def get_data(filters):
	conditions = ""
	values = {}

	if filters.get("project"):
		conditions += " AND name = %(project)s"
		values["project"] = filters["project"]

	projects = frappe.db.sql(
		f"""
		SELECT name, project_name, project_budget, start_date, expected_end_date,
			COALESCE(total_cost, 0) as total_cost
		FROM `tabProject`
		WHERE status = 'In Progress' {conditions}
		ORDER BY project_name
	""",
		values,
		as_dict=True,
	)

	current_date = getdate(today())
	data = []

	for p in projects:
		days_elapsed = max(date_diff(current_date, p.start_date), 1)
		daily_burn = flt(p.total_cost) / days_elapsed if days_elapsed > 0 else 0

		days_remaining = 0
		if p.expected_end_date:
			days_remaining = max(date_diff(p.expected_end_date, current_date), 0)

		projected_total = flt(p.total_cost) + (daily_burn * days_remaining)
		projected_overrun = projected_total - flt(p.project_budget) if flt(p.project_budget) else 0

		budget_exhaustion_date = None
		if daily_burn > 0 and flt(p.project_budget) > flt(p.total_cost):
			days_until_exhaustion = int(
				(flt(p.project_budget) - flt(p.total_cost)) / daily_burn
			)
			budget_exhaustion_date = add_days(current_date, days_until_exhaustion)

		data.append({
			"name": p.name,
			"project_name": p.project_name,
			"project_budget": p.project_budget,
			"total_cost": p.total_cost,
			"days_elapsed": days_elapsed,
			"daily_burn_rate": daily_burn,
			"days_remaining": days_remaining,
			"projected_total_cost": projected_total,
			"projected_overrun": max(projected_overrun, 0),
			"budget_exhaustion_date": budget_exhaustion_date,
		})

	return data
