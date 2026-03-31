// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Expense Entry", {
	refresh(frm) {
		// Show approve/reject buttons for Accountant on flagged expenses
		if (
			frm.doc.docstatus === 1 &&
			frm.doc.approval_status === "Pending Approval" &&
			frappe.user_roles.includes("Refractec Accountant")
		) {
			frm.add_custom_button(__("Approve"), function () {
				let d = new frappe.ui.Dialog({
					title: "Approve Expense",
					fields: [
						{
							fieldname: "remarks",
							fieldtype: "Small Text",
							label: "Approval Remarks",
						},
					],
					primary_action_label: "Approve",
					primary_action(values) {
						frappe.call({
							method: "refractec.refractec.doctype.expense_entry.expense_entry.approve_expense",
							args: { name: frm.doc.name, remarks: values.remarks },
							callback() {
								frm.reload_doc();
							},
						});
						d.hide();
					},
				});
				d.show();
			}).addClass("btn-primary");

			frm.add_custom_button(__("Reject"), function () {
				let d = new frappe.ui.Dialog({
					title: "Reject Expense",
					fields: [
						{
							fieldname: "remarks",
							fieldtype: "Small Text",
							label: "Rejection Reason",
							reqd: 1,
						},
					],
					primary_action_label: "Reject",
					primary_action(values) {
						frappe.call({
							method: "refractec.refractec.doctype.expense_entry.expense_entry.reject_expense",
							args: { name: frm.doc.name, remarks: values.remarks },
							callback() {
								frm.reload_doc();
							},
						});
						d.hide();
					},
				});
				d.show();
			}).addClass("btn-danger");
		}

		// Show flag reason prominently
		if (frm.doc.is_flagged) {
			frm.set_intro(
				__("This expense is flagged: {0}", [frm.doc.flag_reason]),
				"orange"
			);
		}

		if (frm.doc.approval_status === "Auto Approved") {
			frm.set_intro(__("Auto Approved"), "green");
		} else if (frm.doc.approval_status === "Manually Approved") {
			frm.set_intro(
				__("Manually Approved by {0}", [frm.doc.approved_by]),
				"green"
			);
		} else if (frm.doc.approval_status === "Rejected") {
			frm.set_intro(__("Rejected: {0}", [frm.doc.approval_remarks]), "red");
		}
	},
});
