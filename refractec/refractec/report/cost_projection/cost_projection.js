// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Cost Projection"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
	],
};
