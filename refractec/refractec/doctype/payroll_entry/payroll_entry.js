// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Payroll Entry", {
	refresh(frm) {
		if (frm.is_new()) {
			frm.toggle_display("section_break_details", false);
			frm.toggle_display("payroll_details", false);
			frm.toggle_display("section_break_earnings", false);
			frm.toggle_display("section_break_deductions", false);
		}
		frm.trigger("toggle_generate_button");
		frm.trigger("setup_component_filters");
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
	setup_component_filters(frm) {
		// Filter earnings to only Earning-type components
		frm.set_query("salary_component", "earnings", function () {
			return { filters: { component_type: "Earning", enabled: 1 } };
		});
		// Filter deductions to only Deduction-type components
		frm.set_query("salary_component", "deductions", function () {
			return { filters: { component_type: "Deduction", enabled: 1 } };
		});
		// Filter worker in earnings/deductions to only workers in payroll_details
		var payroll_workers = (frm.doc.payroll_details || []).map(function (r) {
			return r.worker;
		});
		frm.set_query("worker", "earnings", function () {
			return { filters: { name: ["in", payroll_workers] } };
		});
		frm.set_query("worker", "deductions", function () {
			return { filters: { name: ["in", payroll_workers] } };
		});
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

// Recalculate when other_deductions changes on a Payroll Detail row
frappe.ui.form.on("Payroll Detail", {
	other_deductions(frm) {
		frm.trigger("recalc_from_components");
	},
});

// Earnings child table events
frappe.ui.form.on("Payroll Earning", {
	salary_component(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.salary_component) {
			frappe.db.get_value("Salary Component", row.salary_component, "default_amount", function (r) {
				if (r && flt(r.default_amount) > 0) {
					frappe.model.set_value(cdt, cdn, "amount", r.default_amount);
				}
			});
		}
	},
	amount(frm) {
		frm.trigger("recalc_from_components");
	},
	earnings_remove(frm) {
		frm.trigger("recalc_from_components");
	},
});

// Deductions child table events
frappe.ui.form.on("Payroll Deduction", {
	salary_component(frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.salary_component) {
			frappe.db.get_value("Salary Component", row.salary_component, "default_amount", function (r) {
				if (r && flt(r.default_amount) > 0) {
					frappe.model.set_value(cdt, cdn, "amount", r.default_amount);
				}
			});
		}
	},
	amount(frm) {
		frm.trigger("recalc_from_components");
	},
	deductions_remove(frm) {
		frm.trigger("recalc_from_components");
	},
});

// Shared recalculation triggered from any component change
frappe.ui.form.on("Payroll Entry", {
	recalc_from_components(frm) {
		// Aggregate earnings per worker
		var worker_earnings = {};
		(frm.doc.earnings || []).forEach(function (r) {
			worker_earnings[r.worker] = flt(worker_earnings[r.worker]) + flt(r.amount);
		});

		// Aggregate deductions per worker
		var worker_deductions = {};
		(frm.doc.deductions || []).forEach(function (r) {
			worker_deductions[r.worker] = flt(worker_deductions[r.worker]) + flt(r.amount);
		});

		// Update each payroll detail row
		(frm.doc.payroll_details || []).forEach(function (row) {
			row.total_earnings = flt(worker_earnings[row.worker]);
			row.total_deductions = flt(worker_deductions[row.worker]);
			row.gross_pay = flt(row.gross_wage) + flt(row.overtime_amount) + flt(row.total_earnings);
			row.net_pay = flt(row.gross_pay) - flt(row.advance_deduction) - flt(row.total_deductions) - flt(row.other_deductions);
		});

		// Update summary totals
		frm.doc.total_gross_pay = (frm.doc.payroll_details || []).reduce(function (s, r) { return s + flt(r.gross_pay); }, 0);
		frm.doc.total_earnings = (frm.doc.payroll_details || []).reduce(function (s, r) { return s + flt(r.total_earnings); }, 0);
		frm.doc.total_advance_deduction = (frm.doc.payroll_details || []).reduce(function (s, r) { return s + flt(r.advance_deduction); }, 0);
		frm.doc.total_deductions = (frm.doc.payroll_details || []).reduce(function (s, r) { return s + flt(r.total_deductions); }, 0);
		frm.doc.total_net_pay = (frm.doc.payroll_details || []).reduce(function (s, r) { return s + flt(r.net_pay); }, 0);

		frm.refresh_fields();
	},
});
