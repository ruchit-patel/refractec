# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

"""
API endpoints for the Supervisor Mobile Frontend.
All endpoints are whitelisted and accessible via /api/method/refractec.api.<method>
"""

import frappe
from frappe.utils import flt, getdate, now_datetime, today


@frappe.whitelist()
def get_supervisor_context():
	"""Get the logged-in supervisor's assigned project and worker list.
	Returns project info, workers, today's attendance status, and cutoff time.
	"""
	user = frappe.session.user
	if user == "Guest":
		frappe.throw("Please login first", frappe.AuthenticationError)

	# Find Worker record linked to this user (by email or user field)
	worker = _get_worker_for_user(user)
	if not worker:
		frappe.throw("No Worker record found for your account")

	if worker.worker_type != "Supervisor":
		frappe.throw("Only Supervisors can access this app")

	# Get assigned project (from User Permission or current_project)
	project = _get_supervisor_project(user, worker)
	if not project:
		frappe.throw("No active project assigned to you")

	project_doc = frappe.get_doc("Project", project)

	# Get assigned workers for this project
	workers = []
	for row in project_doc.worker_assignments:
		if row.is_active:
			workers.append({
				"worker": row.worker,
				"worker_name": row.worker_name,
				"worker_type": row.worker_type,
			})

	# Check today's attendance status
	today_attendance = frappe.db.get_value(
		"Daily Attendance",
		{"project": project, "attendance_date": today(), "docstatus": ["!=", 2]},
		["name", "docstatus"],
		as_dict=True,
	)

	attendance_submitted = False
	attendance_name = None
	if today_attendance:
		attendance_name = today_attendance.name
		attendance_submitted = today_attendance.docstatus == 1

	# Get today's attendance details if they exist
	today_records = {}
	if attendance_name:
		details = frappe.get_all(
			"Attendance Detail",
			filters={"parent": attendance_name},
			fields=["worker", "status", "overtime_hours"],
		)
		for d in details:
			today_records[d.worker] = {
				"status": d.status,
				"overtime_hours": d.overtime_hours,
			}

	# Cutoff check
	cutoff_hour = project_doc.attendance_cutoff_hour or 20
	current_hour = now_datetime().hour
	is_past_cutoff = current_hour >= cutoff_hour

	return {
		"supervisor": {
			"name": worker.name,
			"worker_name": worker.worker_name,
		},
		"project": {
			"name": project_doc.name,
			"project_name": project_doc.project_name,
		},
		"workers": workers,
		"today_attendance": today_records,
		"attendance_submitted": attendance_submitted,
		"attendance_name": attendance_name,
		"cutoff_hour": cutoff_hour,
		"is_past_cutoff": is_past_cutoff,
		"max_ot_hours": int(project_doc.max_overtime_hours_per_day or 4),
		"today": today(),
	}


@frappe.whitelist()
def submit_attendance(project, attendance_data):
	"""Submit daily attendance for a project.

	Args:
		project: Project name
		attendance_data: JSON list of {worker, status} where status is "Present" or "Absent"
	"""
	import json

	if isinstance(attendance_data, str):
		attendance_data = json.loads(attendance_data)

	# Check if attendance already submitted today
	existing = frappe.db.get_value(
		"Daily Attendance",
		{"project": project, "attendance_date": today(), "docstatus": 1},
		"name",
	)
	if existing:
		frappe.throw(f"Attendance already submitted for today: {existing}")

	# Check cutoff
	project_doc = frappe.get_doc("Project", project)
	cutoff_hour = project_doc.attendance_cutoff_hour or 20
	current_hour = now_datetime().hour
	if current_hour >= cutoff_hour:
		frappe.throw(
			f"Attendance cutoff time ({cutoff_hour}:00) has passed. "
			"Please contact admin."
		)

	# Check for draft attendance and delete it first
	draft = frappe.db.get_value(
		"Daily Attendance",
		{"project": project, "attendance_date": today(), "docstatus": 0},
		"name",
	)
	if draft:
		frappe.delete_doc("Daily Attendance", draft, force=True)

	# Create and submit attendance
	doc = frappe.get_doc({
		"doctype": "Daily Attendance",
		"project": project,
		"attendance_date": today(),
		"attendance_details": [
			{
				"worker": row["worker"],
				"status": row["status"],
				"overtime_hours": 0,
			}
			for row in attendance_data
		],
	})
	doc.insert()
	doc.submit()

	return {"name": doc.name, "message": "Attendance submitted successfully"}


@frappe.whitelist()
def submit_overtime(project, overtime_data):
	"""Submit overtime hours for today's attendance.

	Args:
		project: Project name
		overtime_data: JSON list of {worker, overtime_hours}
	"""
	import json

	if isinstance(overtime_data, str):
		overtime_data = json.loads(overtime_data)

	# Find today's submitted attendance
	att_name = frappe.db.get_value(
		"Daily Attendance",
		{"project": project, "attendance_date": today(), "docstatus": 1},
		"name",
	)
	if not att_name:
		frappe.throw("No submitted attendance found for today. Submit attendance first.")

	att_doc = frappe.get_doc("Daily Attendance", att_name)

	# Amend the attendance
	amended = frappe.copy_doc(att_doc)
	amended.amended_from = att_doc.name
	att_doc.cancel()

	# Update overtime hours
	ot_map = {row["worker"]: int(row["overtime_hours"]) for row in overtime_data}
	for row in amended.attendance_details:
		if row.worker in ot_map:
			row.overtime_hours = ot_map[row.worker]

	amended.insert()
	amended.submit()

	return {"name": amended.name, "message": "Overtime submitted successfully"}


@frappe.whitelist()
def create_expense(project, expense_type, amount, description=None, expense_date=None):
	"""Create an expense entry as draft (Step 1).
	Frontend should upload bill attachment next, then call finalize_expense.

	Args:
		project: Project name
		expense_type: Expense Type name
		amount: Amount
		description: Optional description
		expense_date: Optional expense date (defaults to today)
	"""
	user = frappe.session.user
	worker = _get_worker_for_user(user)
	if not worker:
		frappe.throw("No Worker record found for your account")

	doc = frappe.get_doc({
		"doctype": "Expense Entry",
		"project": project,
		"expense_type": expense_type,
		"expense_date": expense_date or today(),
		"posting_date": today(),
		"amount": flt(amount),
		"submitted_by": worker.name,
		"description": description or "",
	})
	doc.insert()

	return {
		"name": doc.name,
		"message": "Expense created as draft. Upload bill and finalize.",
	}


@frappe.whitelist()
def finalize_expense(expense_name):
	"""Submit a draft expense entry (Step 2 — after file upload).
	Picks up any attached files and sets bill_attachment before submitting.
	"""
	doc = frappe.get_doc("Expense Entry", expense_name)

	if doc.docstatus != 0:
		frappe.throw("Expense is already submitted")

	# Pick up file attached via upload
	if not doc.bill_attachment:
		file_url = frappe.db.get_value(
			"File",
			{"attached_to_doctype": "Expense Entry", "attached_to_name": expense_name},
			"file_url",
			order_by="creation desc",
		)
		if file_url:
			doc.bill_attachment = file_url

	doc.submit()

	return {
		"name": doc.name,
		"approval_status": doc.approval_status,
		"message": f"Expense submitted. Status: {doc.approval_status}",
	}


@frappe.whitelist()
def submit_advance(project, worker, amount, payment_mode="Cash", reference_no=None, purpose=None):
	"""Submit a worker advance from the supervisor frontend.

	Args:
		project: Project name
		worker: Worker name (ID)
		amount: Advance amount
		payment_mode: Cash / Bank Transfer / UPI
		reference_no: Reference number for non-cash payments
		purpose: Optional purpose text
	"""
	user = frappe.session.user
	supervisor = _get_worker_for_user(user)
	if not supervisor:
		frappe.throw("No Worker record found for your account")
	if supervisor.worker_type != "Supervisor":
		frappe.throw("Only Supervisors can give advances")

	doc = frappe.get_doc({
		"doctype": "Worker Advance",
		"project": project,
		"worker": worker,
		"advance_date": today(),
		"amount": flt(amount),
		"given_by": supervisor.name,
		"payment_mode": payment_mode or "Cash",
		"reference_no": reference_no or "",
		"purpose": purpose or "",
	})
	doc.insert()
	doc.submit()

	return {
		"name": doc.name,
		"message": f"Advance of ₹{amount} given to {doc.worker_name}",
	}


@frappe.whitelist()
def get_advance_history(project, worker=None):
	"""Get advance history for a project, optionally filtered by worker.

	Args:
		project: Project name
		worker: Optional worker ID to filter by
	"""
	filters = {"project": project, "docstatus": 1}
	if worker:
		filters["worker"] = worker

	advances = frappe.get_all(
		"Worker Advance",
		filters=filters,
		fields=[
			"name", "worker", "worker_name", "advance_date", "amount",
			"payment_mode", "purpose", "recovery_status", "recovered_amount",
			"given_by_name",
		],
		order_by="advance_date desc",
		limit=50,
	)

	# Calculate totals
	total_advanced = sum(flt(a.amount) for a in advances)
	total_recovered = sum(flt(a.recovered_amount) for a in advances)
	total_outstanding = total_advanced - total_recovered

	return {
		"advances": advances,
		"total_advanced": total_advanced,
		"total_recovered": total_recovered,
		"total_outstanding": total_outstanding,
	}


@frappe.whitelist()
def get_expense_types():
	"""Get list of enabled expense types."""
	return frappe.get_all(
		"Expense Type",
		filters={"enabled": 1},
		fields=["name", "expense_type_name"],
		order_by="expense_type_name asc",
	)


# --- Helper functions ---


def _get_worker_for_user(user):
	"""Find the Worker record associated with a User.
	Matches by linked user field or email.
	"""
	# Try finding by a user_id field on Worker if it exists
	worker_name = frappe.db.get_value("Worker", {"user_id": user}, "name")

	if not worker_name:
		# Fallback: try matching by email in mobile_no (since some setups use email there)
		worker_name = frappe.db.get_value("Worker", {"mobile_no": user}, "name")

	if not worker_name:
		# Last resort: find by worker_name matching user's full name
		full_name = frappe.db.get_value("User", user, "full_name")
		if full_name:
			worker_name = frappe.db.get_value("Worker", {"worker_name": full_name}, "name")

	if worker_name:
		return frappe.get_doc("Worker", worker_name)
	return None


def _get_supervisor_project(user, worker):
	"""Get the active project for a supervisor."""
	# First try current_project on worker master
	if worker.current_project:
		project_status = frappe.db.get_value("Project", worker.current_project, "status")
		if project_status in ("Open", "In Progress"):
			return worker.current_project

	# Then try User Permission
	permitted = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Project"},
		pluck="for_value",
	)

	for p in permitted:
		status = frappe.db.get_value("Project", p, "status")
		if status in ("Open", "In Progress"):
			return p

	# Lastly: find projects where this worker is assigned as active supervisor
	result = frappe.db.sql(
		"""
		SELECT p.name
		FROM `tabProject` p
		JOIN `tabProject Worker Assignment` pwa ON pwa.parent = p.name
		WHERE pwa.worker = %s AND pwa.is_active = 1
		  AND p.status IN ('Open', 'In Progress')
		LIMIT 1
	""",
		worker.name,
	)
	if result:
		return result[0][0]

	return None
