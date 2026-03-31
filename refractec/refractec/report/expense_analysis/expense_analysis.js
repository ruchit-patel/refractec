// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Expense Analysis"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "expense_type",
			label: __("Expense Type"),
			fieldtype: "Link",
			options: "Expense Type",
		},
		{
			fieldname: "approval_status",
			label: __("Approval Status"),
			fieldtype: "Select",
			options: "\nAuto Approved\nPending Approval\nManually Approved\nRejected",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
		},
	],
};
