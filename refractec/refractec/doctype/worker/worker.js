// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Worker", {
	refresh(frm) {
		if (frm.doc.worker_type === "Supervisor") {
			frm.set_intro("This worker is a Supervisor and can submit advances and expenses.");
		}
	},
});
