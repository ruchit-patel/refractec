app_name = "refractec"
app_title = "Refractec"
app_publisher = "Ruchit"
app_description = "Construction Project Cost Management System"
app_email = "ruchit@refractec.com"
app_license = "mit"

# Installation
# ------------
after_install = "refractec.setup.after_install"

# Permissions
# -----------
permission_query_conditions = {
	"Daily Attendance": "refractec.refractec.doctype.daily_attendance.daily_attendance.get_permission_query_conditions",
	"Worker Advance": "refractec.refractec.doctype.worker_advance.worker_advance.get_permission_query_conditions",
	"Expense Entry": "refractec.refractec.doctype.expense_entry.expense_entry.get_permission_query_conditions",
}

has_permission = {
	"Daily Attendance": "refractec.refractec.doctype.daily_attendance.daily_attendance.has_permission",
	"Worker Advance": "refractec.refractec.doctype.worker_advance.worker_advance.has_permission",
	"Expense Entry": "refractec.refractec.doctype.expense_entry.expense_entry.has_permission",
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"cron": {
		# Attendance reminder at 12 PM (midday nudge)
		"0 12 * * *": [
			"refractec.refractec.tasks.check_attendance_compliance",
		],
		# Deposit overdue check at 9 AM
		"0 9 * * *": [
			"refractec.refractec.tasks.check_overdue_deposits",
		],
	},
}

# Fixtures
# --------
fixtures = [
	{
		"dt": "Role",
		"filters": [
			["name", "in", ["Refractec Admin", "Refractec Supervisor", "Refractec Accountant"]]
		],
	},
]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------
# Advance Ledger Entry is system-generated and should not block deletion
ignore_links_on_delete = ["Advance Ledger Entry"]

# Exempt linked doctypes from being automatically cancelled
auto_cancel_exempted_doctypes = ["Advance Ledger Entry"]

website_route_rules = [{'from_route': '/frontend/<path:app_path>', 'to_route': 'frontend'},]

# Boot session — hide non-Refractec desktop icons for Refractec-only users
boot_session = "refractec.boot.boot_session"