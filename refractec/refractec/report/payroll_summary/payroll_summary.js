// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Payroll Summary"] = {
	filters: [
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
		{
			fieldname: "payroll_year",
			label: __("Year"),
			fieldtype: "Int",
			default: new Date().getFullYear(),
		},
	],
};
