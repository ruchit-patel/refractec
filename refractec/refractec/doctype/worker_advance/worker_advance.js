// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Worker Advance", {
	project(frm) {
		// Filter workers to only those assigned to the selected project
		frm.set_query("worker", function () {
			return {
				query: "frappe.client.get_list",
				filters: {
					doctype: "Project Worker Assignment",
					filters: { parent: frm.doc.project, is_active: 1 },
					fields: ["worker"],
				},
			};
		});
	},
	refresh(frm) {
		// Filter given_by to only Supervisors
		frm.set_query("given_by", function () {
			return {
				filters: { worker_type: "Supervisor", status: "Active" },
			};
		});
	},
});
