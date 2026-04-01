// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Bank Transfer Sheet"] = {
	filters: [
		{
			fieldname: "payroll_month",
			label: __("Payroll Month"),
			fieldtype: "Select",
			options: "\nJanuary\nFebruary\nMarch\nApril\nMay\nJune\nJuly\nAugust\nSeptember\nOctober\nNovember\nDecember",
			reqd: 1,
			default: [
				"January", "February", "March", "April", "May", "June",
				"July", "August", "September", "October", "November", "December"
			][new Date().getMonth()],
		},
		{
			fieldname: "payroll_year",
			label: __("Payroll Year"),
			fieldtype: "Int",
			reqd: 1,
			default: new Date().getFullYear(),
		},
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options: "Project",
		},
	],
};
