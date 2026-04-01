// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supervisor Fund Transfer", {
	transfer_type(frm) {
		frm.trigger("auto_fill_amount");
	},
	project(frm) {
		frm.trigger("auto_fill_amount");
	},
	payment_mode(frm) {
		frm.trigger("auto_fill_amount");
	},
	auto_fill_amount(frm) {
		if (!frm.doc.project || frm.doc.transfer_type === "Fund Given") return;

		var field = frm.doc.payment_mode === "Cash" ? "fund_cash_balance" : "fund_bank_balance";
		frappe.db.get_value("Project", frm.doc.project, field, (r) => {
			if (r) {
				frm.set_value("amount", Math.max(r[field], 0));
			}
		});
	},
	refresh(frm) {
		frm.set_query("supervisor", function () {
			return {
				filters: { worker_type: "Supervisor", status: "Active" },
			};
		});
		frm.set_query("to_project", function () {
			return {
				filters: {
					status: ["in", ["Open", "In Progress"]],
					name: ["!=", frm.doc.project || ""],
				},
			};
		});
	},
});
