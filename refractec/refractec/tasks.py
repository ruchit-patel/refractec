# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import today, date_diff, getdate, flt


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


def check_overdue_deposits():
	"""Daily: mark deposits as overdue and send email reminders for uncollected deposits."""
	current_date = today()

	# 1. Mark pending deposits as overdue if due_date has passed
	pending_deposits = frappe.get_all(
		"Project Deposit",
		filters={
			"status": ["in", ["Pending", "Partially Collected"]],
			"due_date": ["<", current_date],
		},
		fields=["name", "due_date"],
	)

	for dep in pending_deposits:
		days = date_diff(current_date, dep.due_date)
		frappe.db.set_value("Project Deposit", dep.name, {
			"status": "Overdue" if not frappe.db.get_value("Project Deposit", dep.name, "collected_amount") else "Partially Collected",
			"days_overdue": days,
		}, update_modified=False)

	# 2. Send daily email for all overdue / partially collected deposits
	overdue = frappe.get_all(
		"Project Deposit",
		filters={"status": ["in", ["Overdue", "Partially Collected"]], "due_date": ["<", current_date]},
		fields=[
			"name", "deposit_type", "company_authority", "project",
			"amount", "collected_amount", "due_date", "days_overdue",
			"reference_id",
		],
		order_by="days_overdue desc",
	)

	if not overdue:
		return

	# Build email
	settings = frappe.get_single("Refractec Settings")
	recipients = [
		r.user
		for r in settings.notification_email_recipients
		if r.notification_type in ("Budget Alert", "All")
	]

	# Also get all users with Refractec Admin or Accountant role
	admin_users = frappe.get_all(
		"Has Role",
		filters={"role": ["in", ["Refractec Admin", "Refractec Accountant"]], "parenttype": "User"},
		fields=["parent"],
		distinct=True,
	)
	for u in admin_users:
		if u.parent not in recipients and u.parent != "Administrator":
			recipients.append(u.parent)

	if not recipients:
		return

	total_outstanding = sum(flt(d.amount) - flt(d.collected_amount) for d in overdue)

	# Build HTML table
	rows = ""
	for d in overdue:
		outstanding = flt(d.amount) - flt(d.collected_amount)
		project_name = d.project or "No Project"
		rows += f"""
		<tr>
			<td>{d.name}</td>
			<td>{d.deposit_type}</td>
			<td>{d.company_authority}</td>
			<td>{project_name}</td>
			<td style="text-align:right">₹{flt(d.amount):,.2f}</td>
			<td style="text-align:right">₹{outstanding:,.2f}</td>
			<td>{d.due_date}</td>
			<td style="text-align:center; color:red; font-weight:bold">{d.days_overdue}</td>
		</tr>
		"""

	message = f"""
	<p>The following deposits are <strong>overdue for collection</strong>.
	Total outstanding: <strong>₹{total_outstanding:,.2f}</strong></p>

	<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; font-size:13px; width:100%">
		<thead style="background:#f3f4f6">
			<tr>
				<th>ID</th>
				<th>Type</th>
				<th>Company / Authority</th>
				<th>Project</th>
				<th style="text-align:right">Deposit Amount</th>
				<th style="text-align:right">Outstanding</th>
				<th>Due Date</th>
				<th>Days Overdue</th>
			</tr>
		</thead>
		<tbody>
			{rows}
		</tbody>
	</table>

	<p style="margin-top:16px; font-size:12px; color:#6b7280">
		Please follow up and update the collection status in Refractec.
	</p>
	"""

	frappe.sendmail(
		recipients=list(set(recipients)),
		subject=f"[Reminder] {len(overdue)} Deposit(s) Overdue — ₹{total_outstanding:,.2f} pending",
		message=message,
	)
