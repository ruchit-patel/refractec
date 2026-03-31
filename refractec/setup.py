# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe


def after_install():
	create_number_cards()
	create_dashboard_charts()


def create_number_cards():
	cards = [
		{
			"name": "Active Projects",
			"label": "Active Projects",
			"document_type": "Project",
			"function": "Count",
			"filters_json": '[["Project", "status", "=", "In Progress"]]',
			"is_public": 1,
			"show_percentage_stats": 0,
			"color": "Blue",
		},
		{
			"name": "Pending Expense Approvals",
			"label": "Pending Expense Approvals",
			"document_type": "Expense Entry",
			"function": "Count",
			"filters_json": '[["Expense Entry", "approval_status", "=", "Pending Approval"], ["Expense Entry", "docstatus", "=", 1]]',
			"is_public": 1,
			"show_percentage_stats": 0,
			"color": "Orange",
		},
		{
			"name": "Active Workers",
			"label": "Active Workers",
			"document_type": "Worker",
			"function": "Count",
			"filters_json": '[["Worker", "status", "=", "Active"]]',
			"is_public": 1,
			"show_percentage_stats": 0,
			"color": "Green",
		},
	]

	for card in cards:
		if not frappe.db.exists("Number Card", card["name"]):
			doc = frappe.new_doc("Number Card")
			doc.update(card)
			doc.insert(ignore_permissions=True)

	frappe.db.commit()


def create_dashboard_charts():
	charts = [
		{
			"name": "Budget Utilization by Project",
			"chart_name": "Budget Utilization by Project",
			"chart_type": "Report",
			"report_name": "Project Cost Summary",
			"is_public": 1,
			"filters_json": "{}",
			"type": "Bar",
			"use_report_chart": 1,
			"timeseries": 0,
		},
		{
			"name": "Expense Type Distribution",
			"chart_name": "Expense Type Distribution",
			"chart_type": "Report",
			"report_name": "Expense Analysis",
			"is_public": 1,
			"filters_json": "{}",
			"type": "Pie",
			"use_report_chart": 1,
			"timeseries": 0,
		},
	]

	for chart in charts:
		if not frappe.db.exists("Dashboard Chart", chart["name"]):
			doc = frappe.new_doc("Dashboard Chart")
			doc.update(chart)
			doc.insert(ignore_permissions=True)

	frappe.db.commit()
