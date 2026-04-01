// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.toggle_display("section_break_details", false);
			frm.toggle_display("payroll_details", false);
		}
		frm.trigger("toggle_generate_button");
	},
	project(frm) {
		frm.trigger("toggle_generate_button");
	},
	payroll_month(frm) {
		frm.trigger("toggle_generate_button");
	},
	payroll_year(frm) {
		frm.trigger("toggle_generate_button");
	},
	toggle_generate_button(frm) {
		frm.remove_custom_button(__("Generate Payroll"));

		if (
			frm.doc.docstatus === 0 &&
			frm.doc.project &&
			frm.doc.payroll_month &&
			frm.doc.payroll_year
		) {
			frm.add_custom_button(__("Generate Payroll"), function () {
				if (frm.is_new()) {
					frappe.call({
						method: "refractec.refractec.doctype.payroll_entry.payroll_entry.create_and_generate_payroll",
						args: {
							project: frm.doc.project,
							payroll_month: frm.doc.payroll_month,
							payroll_year: frm.doc.payroll_year,
						},
						freeze: true,
						freeze_message: __("Generating Payroll..."),
						callback: function (r) {
							if (r.message) {
								frappe.set_route("Form", "Payroll Entry", r.message);
							}
						},
					});
				} else {
					frappe.call({
						method: "generate_payroll",
						doc: frm.doc,
						freeze: true,
						freeze_message: __("Generating Payroll..."),
						callback: function () {
							frm.reload_doc();
						},
					});
				}
			}).addClass("btn-primary");
		}
	},
});

frappe.ui.form.on("Payroll Detail", {
	other_deductions(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		row.net_pay = flt(row.gross_pay) - flt(row.advance_deduction) - flt(row.other_deductions);
		frm.refresh_field("payroll_details");

		frm.doc.total_net_pay = frm.doc.payroll_details.reduce(function (sum, r) {
			return sum + flt(r.net_pay);
		}, 0);
		frm.refresh_field("total_net_pay");
	},
});
