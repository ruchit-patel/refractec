# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days


class TestDailyAttendance(IntegrationTestCase):
	def setUp(self):
		self.setup_test_data()

	def setup_test_data(self):
		"""Create test worker, profile, and project"""
		# Expense Type
		if not frappe.db.exists("Expense Type", "Test Material"):
			frappe.get_doc({"doctype": "Expense Type", "expense_type_name": "Test Material"}).insert()

		# Profile
		if not frappe.db.exists("Project Configuration Profile", "Test Attendance Profile"):
			frappe.get_doc({
				"doctype": "Project Configuration Profile",
				"profile_name": "Test Attendance Profile",
				"max_overtime_hours_per_day": 4,
				"expense_cutoff_days": 3,
				"expense_range_rules": [
					{"expense_type": "Test Material", "min_amount": 100, "max_amount": 5000},
				],
			}).insert()

		# Workers
		self.worker = self._get_or_create_worker("Att Test Worker", "Worker", 500, 100)
		self.supervisor = self._get_or_create_worker("Att Test Supervisor", "Supervisor", 800, 150)

		# Project
		if not frappe.db.exists("Project", {"project_name": "Test Att Project"}):
			self.project = frappe.get_doc({
				"doctype": "Project",
				"project_name": "Test Att Project",
				"start_date": "2026-01-01",
				"configuration_profile": "Test Attendance Profile",
				"project_budget": 100000,
				"worker_assignments": [
					{
						"worker": self.worker,
						"worker_name": "Att Test Worker",
						"worker_type": "Worker",
						"daily_wage_rate": 500,
						"overtime_hourly_rate": 100,
						"is_active": 1,
					},
					{
						"worker": self.supervisor,
						"worker_name": "Att Test Supervisor",
						"worker_type": "Supervisor",
						"daily_wage_rate": 800,
						"overtime_hourly_rate": 150,
						"is_active": 1,
					},
				],
			}).insert()
			self.project_name = self.project.name
		else:
			self.project_name = frappe.db.get_value("Project", {"project_name": "Test Att Project"}, "name")

	def _get_or_create_worker(self, name, worker_type, daily_rate, ot_rate):
		existing = frappe.db.get_value("Worker", {"worker_name": name}, "name")
		if existing:
			return existing
		w = frappe.get_doc({
			"doctype": "Worker",
			"worker_name": name,
			"worker_type": worker_type,
			"date_of_joining": "2026-01-01",
			"daily_wage_rate": daily_rate,
			"overtime_hourly_rate": ot_rate,
		}).insert()
		return w.name

	def test_attendance_creates_successfully(self):
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": add_days(today(), -10),
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Att Test Worker",
					"status": "Present",
					"overtime_hours": 2,
				},
			],
		})
		att.insert()
		att.submit()

		# Verify wage computation
		row = att.attendance_details[0]
		self.assertEqual(row.computed_wage, 500)
		self.assertEqual(row.computed_ot_amount, 200)
		self.assertEqual(row.total_for_day, 700)

	def test_half_day_wage(self):
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": add_days(today(), -11),
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Att Test Worker",
					"status": "Half Day",
					"overtime_hours": 0,
				},
			],
		})
		att.insert()

		row = att.attendance_details[0]
		self.assertEqual(row.computed_wage, 250)

	def test_duplicate_attendance_blocked(self):
		date = add_days(today(), -12)
		att1 = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": date,
			"attendance_details": [
				{"worker": self.worker, "worker_name": "Att Test Worker", "status": "Present"},
			],
		})
		att1.insert()

		att2 = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": date,
			"attendance_details": [
				{"worker": self.worker, "worker_name": "Att Test Worker", "status": "Absent"},
			],
		})
		self.assertRaises(frappe.ValidationError, att2.insert)

	def test_overtime_exceeds_max(self):
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": add_days(today(), -13),
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Att Test Worker",
					"status": "Present",
					"overtime_hours": 10,  # exceeds max of 4
				},
			],
		})
		self.assertRaises(frappe.ValidationError, att.insert)

	def test_absent_worker_cannot_have_overtime(self):
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": add_days(today(), -14),
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Att Test Worker",
					"status": "Absent",
					"overtime_hours": 2,
				},
			],
		})
		self.assertRaises(frappe.ValidationError, att.insert)
