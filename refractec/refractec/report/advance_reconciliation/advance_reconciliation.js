// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Advance Reconciliation"] = {
	filters: [
		{
			fieldname: "worker",
			label: __("Worker"),
			fieldtype: "Link",
			options: "Worker",
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
	],
};
