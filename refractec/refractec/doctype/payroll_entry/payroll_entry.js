// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.doc.docstatus === 0 && frm.doc.project && frm.doc.payroll_month && frm.doc.payroll_year) {
			frm.add_custom_button(__("Generate Payroll"), function () {
				frm.call("generate_payroll").then(() => {
					frm.refresh_fields();
				});
			}).addClass("btn-primary");
		}
	},
});
