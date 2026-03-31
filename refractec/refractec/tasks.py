# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today


def check_attendance_compliance():
	"""Check which active projects have missing attendance for today and notify"""
	settings = frappe.get_single("Refractec Settings")
	if not settings.enable_attendance_reminders:
		return

	current_date = today()
	active_projects = frappe.get_all(
		"Project",
		filters={"status": "In Progress"},
		fields=["name", "project_name"],
	)

	for project in active_projects:
		attendance_exists = frappe.db.exists("Daily Attendance", {
			"project": project.name,
			"attendance_date": current_date,
			"docstatus": ["!=", 2],
		})

		if attendance_exists:
			continue

		# Get supervisor emails from project worker assignments
		supervisors = frappe.db.sql(
			"""
			SELECT DISTINCT u.name as email
			FROM `tabProject Worker Assignment` pwa
			JOIN `tabWorker` w ON w.name = pwa.worker
			JOIN `tabUser` u ON u.name = w.mobile_no OR u.email = w.mobile_no
			WHERE pwa.parent = %s AND pwa.is_active = 1
			  AND w.worker_type = 'Supervisor'
		""",
			project.name,
			as_dict=True,
		)

		admin_recipients = [
			r.user
			for r in settings.notification_email_recipients
			if r.notification_type in ("Attendance Reminder", "All")
		]

		recipients = admin_recipients + [s.email for s in supervisors if s.email]

		if recipients:
			frappe.sendmail(
				recipients=list(set(recipients)),
				subject=f"Attendance Missing: {project.project_name}",
				message=f"""
					<p>Daily attendance for project
					<strong>{project.project_name}</strong> ({project.name})
					has not been entered for <strong>{current_date}</strong>.</p>
					<p>Please submit attendance at the earliest.</p>
				""",
			)
