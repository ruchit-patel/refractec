// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project Deposit", {
	refresh(frm) {
		// Show status indicator
		if (frm.doc.status === "Overdue") {
			frm.dashboard.set_headline(
				__("Overdue by {0} days — ₹{1} pending collection", [
					frm.doc.days_overdue,
					(flt(frm.doc.amount) - flt(frm.doc.collected_amount)).toLocaleString("en-IN"),
				]),
				"red"
			);
		} else if (frm.doc.status === "Collected") {
			frm.dashboard.set_headline(__("Deposit fully collected"), "green");
		}

		// Mark as Forfeited button
		if (frm.doc.status !== "Collected" && frm.doc.status !== "Forfeited") {
			frm.add_custom_button(__("Mark as Forfeited"), function () {
				frappe.confirm(
					__("Are you sure this deposit is forfeited and cannot be collected?"),
					function () {
						frm.set_value("status", "Forfeited");
						frm.save();
					}
				);
			});
		}

		// Re-open from Forfeited
		if (frm.doc.status === "Forfeited") {
			frm.add_custom_button(__("Re-open"), function () {
				frm.set_value("status", "Pending");
				frm.save();
			});
		}
	},

	collected_amount(frm) {
		// Auto-set collection date when amount is entered
		if (flt(frm.doc.collected_amount) > 0 && !frm.doc.collection_date) {
			frm.set_value("collection_date", frappe.datetime.nowdate());
		}
	},
});
