// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Worker Wise Advance Balance"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "worker",
			label: __("Worker"),
			fieldtype: "Link",
			options: "Worker",
		},
	],
};
