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
def get_my_expenses(project):
	"""Get all expenses submitted by the logged-in supervisor for a project."""
	user = frappe.session.user
	worker = _get_worker_for_user(user)
	if not worker:
		frappe.throw("No Worker record found for your account")

	expenses = frappe.get_all(
		"Expense Entry",
		filters={"project": project, "submitted_by": worker.name, "docstatus": ["!=", 2]},
		fields=[
			"name", "expense_type", "expense_date", "amount", "description",
			"approval_status", "is_flagged", "flag_reason", "bill_attachment",
			"posting_date", "docstatus",
		],
		order_by="expense_date desc",
		limit=50,
	)

	# Fetch expense type names
	for e in expenses:
		e.expense_type_name = frappe.db.get_value("Expense Type", e.expense_type, "expense_type_name") or e.expense_type

	return expenses


@frappe.whitelist()
def edit_expense(expense_name, expense_type=None, amount=None, description=None, expense_date=None):
	"""Edit a submitted expense by amending it. The amended expense is always flagged.

	Args:
		expense_name: Original Expense Entry name
		expense_type: New expense type (optional)
		amount: New amount (optional)
		description: New description (optional)
		expense_date: New expense date (optional)
	"""
	user = frappe.session.user
	worker = _get_worker_for_user(user)
	if not worker:
		frappe.throw("No Worker record found for your account")

	original = frappe.get_doc("Expense Entry", expense_name)

	if original.submitted_by != worker.name:
		frappe.throw("You can only edit expenses you submitted")

	if original.docstatus != 1:
		frappe.throw("Only submitted expenses can be edited")

	# Cancel original
	original.cancel()

	# Create amended copy
	amended = frappe.copy_doc(original)
	amended.amended_from = original.name

	# Apply changes
	if expense_type:
		amended.expense_type = expense_type
	if amount is not None:
		amended.amount = flt(amount)
	if description is not None:
		amended.description = description
	if expense_date:
		amended.expense_date = expense_date

	# Flag the edited expense
	amended.is_flagged = 1
	amended.flag_reason = f"Edited by {worker.worker_name} on {today()}"

	# Copy bill attachment from original if it had one
	if original.bill_attachment and not amended.bill_attachment:
		amended.bill_attachment = original.bill_attachment

	amended.insert()
	amended.submit()

	return {
		"name": amended.name,
		"approval_status": amended.approval_status,
		"message": f"Expense updated and flagged. Status: {amended.approval_status}",
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


# --- Admin Dashboard ---


@frappe.whitelist()
def get_admin_dashboard_data():
	"""Return all data needed for the admin dashboard."""
	from frappe.utils import add_months

	now = getdate()
	today_date = today()

	# --- Summary cards ---
	active_workers = frappe.db.count("Worker", {"status": "Active"})
	active_projects = frappe.db.count("Project", {"status": ["in", ["Open", "In Progress"]]})

	todays_ot = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(ad.overtime_hours), 0)
		FROM `tabAttendance Detail` ad
		JOIN `tabDaily Attendance` da ON da.name = ad.parent
		WHERE da.attendance_date = %s AND da.docstatus = 1
	""", today_date)[0][0])

	pending_approvals = frappe.db.count("Expense Entry", {
		"docstatus": 1,
		"approval_status": ["in", ["Pending", "Pending Approval"]],
	})

	month_names = [
		"January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December",
	]
	payroll_month = month_names[now.month - 1]
	payroll_this_month = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(total_net_pay), 0) FROM `tabPayroll Entry`
		WHERE payroll_month = %s AND payroll_year = %s AND docstatus = 1
	""", (payroll_month, now.year))[0][0])

	outstanding_advances = flt(frappe.db.sql("""
		SELECT COALESCE(SUM(amount - recovered_amount), 0) FROM `tabWorker Advance`
		WHERE docstatus = 1 AND recovery_status != 'Fully Recovered'
	""")[0][0])

	# --- Projects ---
	projects = frappe.get_all("Project",
		filters={"status": ["in", ["Open", "In Progress"]]},
		fields=[
			"name", "project_name", "status", "project_budget",
			"total_cost", "total_labor_cost", "total_expense_cost",
			"budget_utilization_pct", "budget_variance",
			"start_date", "expected_end_date",
			"total_advance_given", "total_advance_recovered",
		],
		order_by="project_name asc",
	)

	for p in projects:
		assignments = frappe.get_all("Project Worker Assignment",
			filters={"parent": p.name, "is_active": 1},
			fields=["worker_type"])
		p.total_workers = len(assignments)
		p.supervisors = sum(1 for a in assignments if a.worker_type == "Supervisor")
		p.workers = p.total_workers - p.supervisors

		p.todays_ot = flt(frappe.db.sql("""
			SELECT COALESCE(SUM(ad.overtime_hours), 0)
			FROM `tabAttendance Detail` ad
			JOIN `tabDaily Attendance` da ON da.name = ad.parent
			WHERE da.project = %s AND da.attendance_date = %s AND da.docstatus = 1
		""", (p.name, today_date))[0][0])

		p.expenses_this_month = flt(frappe.db.sql("""
			SELECT COALESCE(SUM(amount), 0) FROM `tabExpense Entry`
			WHERE project = %s AND docstatus = 1
			AND MONTH(expense_date) = %s AND YEAR(expense_date) = %s
		""", (p.name, now.month, now.year))[0][0])

		if flt(p.budget_utilization_pct) >= 100:
			p.health = "Over Budget"
		elif flt(p.budget_utilization_pct) >= 80:
			p.health = "At Risk"
		else:
			p.health = "On Track"

	# --- Alerts ---
	alerts = []

	for p in projects:
		if p.health == "Over Budget":
			alerts.append({
				"type": "danger",
				"title": f"{p.project_name} — Budget Exceeded",
				"message": f"Utilized {flt(p.budget_utilization_pct):.0f}% of ₹{flt(p.project_budget):,.0f} budget",
				"link": f"/app/project/{p.name}",
			})

	if pending_approvals > 0:
		pending_amount = flt(frappe.db.sql("""
			SELECT COALESCE(SUM(amount), 0) FROM `tabExpense Entry`
			WHERE docstatus = 1 AND approval_status IN ('Pending', 'Pending Approval')
		""")[0][0])
		alerts.append({
			"type": "warning",
			"title": "Pending Expense Approvals",
			"message": f"{pending_approvals} expense(s) totaling ₹{pending_amount:,.0f} awaiting approval",
			"link": "/app/expense-entry?approval_status=Pending+Approval",
		})

	# Attendance compliance — missing today
	projects_with_attendance = frappe.get_all("Daily Attendance",
		filters={"attendance_date": today_date, "docstatus": 1},
		pluck="project")
	for p in projects:
		if p.name not in projects_with_attendance and p.status == "In Progress":
			alerts.append({
				"type": "info",
				"title": f"{p.project_name} — Attendance Missing",
				"message": "Today's attendance has not been submitted yet",
				"link": f"/app/daily-attendance?project={p.name}",
			})

	# --- Expense analytics (last 6 months) ---
	six_months_ago = add_months(today_date, -6)
	expense_rows = frappe.db.sql("""
		SELECT
			DATE_FORMAT(ee.expense_date, '%%b %%Y') as month_label,
			DATE_FORMAT(ee.expense_date, '%%Y-%%m') as month_key,
			et.expense_type_name as expense_type,
			SUM(ee.amount) as total
		FROM `tabExpense Entry` ee
		JOIN `tabExpense Type` et ON ee.expense_type = et.name
		WHERE ee.docstatus = 1 AND ee.expense_date >= %s
		GROUP BY month_key, month_label, et.expense_type_name
		ORDER BY month_key
	""", six_months_ago, as_dict=True)

	months_order = []
	expense_types = set()
	expense_by_month = {}
	for row in expense_rows:
		if row.month_key not in expense_by_month:
			expense_by_month[row.month_key] = {"label": row.month_label, "data": {}}
			months_order.append(row.month_key)
		expense_by_month[row.month_key]["data"][row.expense_type] = flt(row.total)
		expense_types.add(row.expense_type)

	expense_chart = {
		"months": [expense_by_month[m]["label"] for m in months_order],
		"types": sorted(list(expense_types)),
		"data": {expense_by_month[m]["label"]: expense_by_month[m]["data"] for m in months_order},
	}

	# --- Worker distribution ---
	worker_by_project = [
		{"project_name": p.project_name, "count": p.total_workers}
		for p in projects
	]

	# --- Recent activities ---
	recent_expenses = frappe.get_all("Expense Entry",
		filters={"docstatus": 1},
		fields=["name", "project", "amount", "submitted_by_name", "posting_date", "approval_status", "expense_type"],
		order_by="creation desc",
		limit=5)

	recent_advances = frappe.get_all("Worker Advance",
		filters={"docstatus": 1},
		fields=["name", "project", "worker_name", "amount", "advance_date"],
		order_by="creation desc",
		limit=5)

	return {
		"summary": {
			"active_workers": active_workers,
			"active_projects": active_projects,
			"todays_ot_hours": todays_ot,
			"pending_approvals": pending_approvals,
			"payroll_this_month": payroll_this_month,
			"outstanding_advances": outstanding_advances,
		},
		"alerts": alerts,
		"projects": projects,
		"expense_chart": expense_chart,
		"worker_by_project": worker_by_project,
		"recent_expenses": recent_expenses,
		"recent_advances": recent_advances,
	}


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
