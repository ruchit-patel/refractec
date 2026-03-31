// Copyright (c) 2026, Ruchit and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daily Attendance", {
	project(frm) {
		if (frm.doc.project) {
			// Auto-populate attendance details with assigned workers
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Project",
					name: frm.doc.project,
				},
				callback(r) {
					if (r.message) {
						frm.clear_table("attendance_details");
						r.message.worker_assignments.forEach((wa) => {
							if (wa.is_active) {
								let row = frm.add_child("attendance_details");
								row.worker = wa.worker;
								row.worker_name = wa.worker_name;
								row.worker_type = wa.worker_type;
								row.status = "Present";
								row.overtime_hours = 0;
							}
						});
						frm.refresh_field("attendance_details");
					}
				},
			});
		}
	},
});
