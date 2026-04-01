// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		frm.trigger("toggle_mode");
		frm.trigger("setup_filters");
	},

	toggle_mode(frm) {
		var is_auto = !!frm.doc.payroll_entry;

		// Lock all fields if auto-generated from payroll
		var editable_fields = [
			"payroll_entry", "project", "employee_name", "worker", "worker_type",
			"payroll_month", "payroll_year", "from_date", "to_date",
			"total_present_days", "total_overtime_hours",
			"daily_wage_rate", "overtime_hourly_rate", "gross_wage", "overtime_amount",
			"slip_earnings", "slip_deductions",
			"advance_deduction", "other_deductions"
		];

		editable_fields.forEach(function (f) {
			frm.set_df_property(f, "read_only", is_auto ? 1 : 0);
		});

		if (is_auto) {
			frm.set_intro("Auto-generated from Payroll Entry. Fields are read-only.", "blue");
		} else {
			frm.set_intro("");
		}
	},

	setup_filters(frm) {
		frm.set_query("salary_component", "slip_earnings", function () {
			return { filters: { component_type: "Earning", enabled: 1 } };
		});
		frm.set_query("salary_component", "slip_deductions", function () {
			return { filters: { component_type: "Deduction", enabled: 1 } };
		});
	},

	// Auto-fill employee_name from worker
	worker(frm) {
		if (frm.doc.worker) {
			frappe.db.get_value("Worker", frm.doc.worker, ["worker_name", "worker_type"], function (r) {
				if (r) {
					frm.set_value("employee_name", r.worker_name);
					frm.set_value("worker_type", r.worker_type);
				}
			});
		}
	},

	// Recalculate on field changes (manual mode)
	gross_wage(frm) { frm.trigger("recalculate"); },
	overtime_amount(frm) { frm.trigger("recalculate"); },
	advance_deduction(frm) { frm.trigger("recalculate"); },
	other_deductions(frm) { frm.trigger("recalculate"); },

	recalculate(frm) {
		var total_earnings = (frm.doc.slip_earnings || []).reduce(function (s, r) {
			return s + flt(r.amount);
		}, 0);
		var total_deductions = (frm.doc.slip_deductions || []).reduce(function (s, r) {
			return s + flt(r.amount);
		}, 0);

		var gross_pay = flt(frm.doc.gross_wage) + flt(frm.doc.overtime_amount) + total_earnings;
		var total_all_ded = flt(frm.doc.advance_deduction) + total_deductions + flt(frm.doc.other_deductions);
		var net_pay = gross_pay - total_all_ded;

		frm.set_value("total_earnings", total_earnings);
		frm.set_value("total_deductions", total_deductions);
		frm.set_value("gross_pay", gross_pay);
		frm.set_value("total_all_deductions", total_all_ded);
		frm.set_value("net_pay", net_pay);
	},
});

frappe.ui.form.on("Salary Slip Earning", {
	amount(frm) { frm.trigger("recalculate"); },
	slip_earnings_remove(frm) { frm.trigger("recalculate"); },
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
});

frappe.ui.form.on("Salary Slip Deduction", {
	amount(frm) { frm.trigger("recalculate"); },
	slip_deductions_remove(frm) { frm.trigger("recalculate"); },
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
});
