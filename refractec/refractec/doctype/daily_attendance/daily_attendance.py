# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class DailyAttendance(Document):
	def validate(self):
		self.validate_duplicate()
		self.validate_workers_assigned()
		self.validate_overtime()
		self.compute_totals()

	def validate_duplicate(self):
		existing = frappe.db.exists("Daily Attendance", {
			"project": self.project,
			"attendance_date": self.attendance_date,
			"docstatus": ["!=", 2],
			"name": ["!=", self.name],
		})
		if existing:
			frappe.throw(
				f"Attendance for {self.project} on {self.attendance_date} "
				f"already exists: {existing}"
			)

	def validate_workers_assigned(self):
		project = frappe.get_doc("Project", self.project)
		assigned_workers = {
			row.worker for row in project.worker_assignments if row.is_active
		}
		for row in self.attendance_details:
			if row.worker not in assigned_workers:
				frappe.throw(
					f"Worker {row.worker} ({row.worker_name}) is not "
					f"assigned to project {self.project}"
				)

	def validate_overtime(self):
		project = frappe.get_doc("Project", self.project)
		max_ot = flt(project.max_overtime_hours_per_day) or 4

		for row in self.attendance_details:
			if flt(row.overtime_hours) > max_ot:
				frappe.throw(
					f"Overtime hours for {row.worker_name} ({row.overtime_hours}) "
					f"exceed maximum allowed ({max_ot})"
				)
			if row.status == "Absent" and flt(row.overtime_hours) > 0:
				frappe.throw(
					f"Cannot mark overtime for absent worker {row.worker_name}"
				)

	def compute_totals(self):
		for row in self.attendance_details:
			rate = self.get_worker_rate(row.worker)
			row.daily_wage_rate = rate["daily_wage_rate"]
			row.overtime_rate = rate["overtime_hourly_rate"]

			if row.status == "Present":
				row.computed_wage = flt(row.daily_wage_rate)
			elif row.status == "Half Day":
				row.computed_wage = flt(row.daily_wage_rate) / 2
			else:
				row.computed_wage = 0

			row.computed_ot_amount = flt(row.overtime_hours) * flt(row.overtime_rate)
			row.total_for_day = flt(row.computed_wage) + flt(row.computed_ot_amount)

		self.total_present = sum(
			1 for r in self.attendance_details if r.status in ("Present", "Half Day")
		)
		self.total_absent = sum(
			1 for r in self.attendance_details if r.status == "Absent"
		)
		self.total_overtime_hours = sum(
			flt(r.overtime_hours) for r in self.attendance_details
		)

	def get_worker_rate(self, worker_id):
		project = frappe.get_doc("Project", self.project)
		for row in project.worker_assignments:
			if row.worker == worker_id:
				return {
					"daily_wage_rate": flt(row.daily_wage_rate),
					"overtime_hourly_rate": flt(row.overtime_hourly_rate),
				}

		# Fallback to worker master rates
		worker = frappe.get_doc("Worker", worker_id)
		return {
			"daily_wage_rate": flt(worker.daily_wage_rate),
			"overtime_hourly_rate": flt(worker.overtime_hourly_rate),
		}

	def on_submit(self):
		self.update_project_labor_cost()

	def on_cancel(self):
		self.reverse_project_labor_cost()

	def update_project_labor_cost(self):
		total_day_cost = sum(flt(r.total_for_day) for r in self.attendance_details)
		frappe.db.sql(
			"""
			UPDATE `tabProject`
			SET total_labor_cost = COALESCE(total_labor_cost, 0) + %s,
				total_cost = COALESCE(total_labor_cost, 0) + %s + COALESCE(total_expense_cost, 0)
			WHERE name = %s
		""",
			(total_day_cost, total_day_cost, self.project),
		)

	def reverse_project_labor_cost(self):
		total_day_cost = sum(flt(r.total_for_day) for r in self.attendance_details)
		frappe.db.sql(
			"""
			UPDATE `tabProject`
			SET total_labor_cost = COALESCE(total_labor_cost, 0) - %s,
				total_cost = COALESCE(total_labor_cost, 0) - %s + COALESCE(total_expense_cost, 0)
			WHERE name = %s
		""",
			(total_day_cost, total_day_cost, self.project),
		)


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Refractec Admin" in frappe.get_roles(user):
		return ""

	return """(`tabDaily Attendance`.project in (
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
