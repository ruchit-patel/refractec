// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Budget vs Actual"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nIn Progress\nCompleted\nCancelled",
		},
	],
};
