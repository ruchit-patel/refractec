# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate


class WorkerAdvance(Document):
	def validate(self):
		self.validate_supervisor()
		self.validate_worker_assigned()
		self.validate_monthly_limit()

	def validate_supervisor(self):
		worker_type = frappe.db.get_value("Worker", self.given_by, "worker_type")
		if worker_type != "Supervisor":
			frappe.throw(
				f"{self.given_by_name} is not a Supervisor. "
				"Only Supervisors can give advances."
			)

	def validate_worker_assigned(self):
		project = frappe.get_doc("Project", self.project)
		assigned_workers = {
			row.worker for row in project.worker_assignments if row.is_active
		}
		if self.worker not in assigned_workers:
			frappe.throw(
				f"Worker {self.worker} ({self.worker_name}) is not "
				f"assigned to project {self.project}"
			)

	def validate_monthly_limit(self):
		project = frappe.get_doc("Project", self.project)
		if not project.advance_monthly_limit_per_worker:
			return

		month_start = getdate(self.advance_date).replace(day=1)
		month_total = flt(
			frappe.db.sql(
				"""
			SELECT COALESCE(SUM(amount), 0) FROM `tabWorker Advance`
			WHERE project=%s AND worker=%s AND docstatus=1
			  AND advance_date >= %s AND advance_date <= %s
			  AND name != %s
		""",
				(self.project, self.worker, month_start, self.advance_date, self.name),
			)[0][0]
		)

		if (month_total + flt(self.amount)) > flt(
			project.advance_monthly_limit_per_worker
		):
			frappe.throw(
				f"Monthly advance limit of "
				f"{project.advance_monthly_limit_per_worker} exceeded "
				f"for {self.worker_name}. Already given: {month_total}"
			)

	def on_submit(self):
		self.create_ledger_entry()
		self.update_project_advance()

	def on_cancel(self):
		self.reverse_ledger_entry()
		self.reverse_project_advance()

	def create_ledger_entry(self):
		last_balance = self._get_last_balance()

		frappe.get_doc({
			"doctype": "Advance Ledger Entry",
			"project": self.project,
			"worker": self.worker,
			"posting_date": self.advance_date,
			"transaction_type": "Advance Given",
			"amount": self.amount,
			"running_balance": flt(last_balance) + flt(self.amount),
			"reference_doctype": "Worker Advance",
			"reference_name": self.name,
			"remarks": f"Advance given by {self.given_by_name}",
		}).insert(ignore_permissions=True)

	def reverse_ledger_entry(self):
		last_balance = self._get_last_balance()

		frappe.get_doc({
			"doctype": "Advance Ledger Entry",
			"project": self.project,
			"worker": self.worker,
			"posting_date": self.advance_date,
			"transaction_type": "Advance Recovered",
			"amount": self.amount,
			"running_balance": flt(last_balance) - flt(self.amount),
			"reference_doctype": "Worker Advance",
			"reference_name": self.name,
			"remarks": f"Reversal: Advance {self.name} cancelled",
		}).insert(ignore_permissions=True)

	def _get_last_balance(self):
		result = frappe.db.sql(
			"""
			SELECT running_balance FROM `tabAdvance Ledger Entry`
			WHERE project=%s AND worker=%s
			ORDER BY posting_date DESC, creation DESC LIMIT 1
		""",
			(self.project, self.worker),
		)
		return flt(result[0][0]) if result else 0

	def update_project_advance(self):
		project = frappe.get_doc("Project", self.project)
		project.total_advance_given = flt(project.total_advance_given) + flt(self.amount)
		project.save(ignore_permissions=True)

	def reverse_project_advance(self):
		project = frappe.get_doc("Project", self.project)
		project.total_advance_given = flt(project.total_advance_given) - flt(self.amount)
		project.save(ignore_permissions=True)


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Refractec Admin" in frappe.get_roles(user):
		return ""

	return """(`tabWorker Advance`.project in (
		select `for_value` from `tabUser Permission`
		where `user`={user} and `allow`='Project'
	))""".format(user=frappe.db.escape(user))


def has_permission(doc, ptype, user):
	if "Refractec Admin" in frappe.get_roles(user):
		return True

	permitted_projects = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Project"},
		pluck="for_value",
	)
	return doc.project in permitted_projects
