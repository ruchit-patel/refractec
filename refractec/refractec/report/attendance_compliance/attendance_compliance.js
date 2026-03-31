// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.query_reports["Attendance Compliance"] = {
	filters: [
		{
			fieldname: "num_days",
			label: __("Last N Days"),
			fieldtype: "Int",
			default: 7,
		},
	],
};
