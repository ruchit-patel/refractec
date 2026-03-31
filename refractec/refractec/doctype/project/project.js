// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project", {
	refresh(frm) {
		if (frm.doc.budget_utilization_pct >= 95) {
			frm.dashboard.set_headline(
				__("Budget utilization is at {0}% - CRITICAL", [frm.doc.budget_utilization_pct.toFixed(1)]),
				"red"
			);
		} else if (frm.doc.budget_utilization_pct >= 80) {
			frm.dashboard.set_headline(
				__("Budget utilization is at {0}% - Warning", [frm.doc.budget_utilization_pct.toFixed(1)]),
				"orange"
			);
		}
	},
});
