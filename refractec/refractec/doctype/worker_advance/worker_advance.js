// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Worker Advance", {
	refresh(frm) {
		frm.set_query("given_by", function () {
			return {
				filters: { worker_type: "Supervisor", status: "Active" },
			};
		});

		if (frm.doc.project) {
			frm.trigger("project");
		}
	},
	project(frm) {
		if (!frm.doc.project) return;

		frm.set_query("worker", function () {
			return {
				query: "refractec.refractec.doctype.worker_advance.worker_advance.get_project_workers",
				filters: { project: frm.doc.project },
			};
		});
	},
});
