# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days


class TestPayrollEntry(IntegrationTestCase):
	def setUp(self):
		self.setup_test_data()

	def setup_test_data(self):
		if not frappe.db.exists("Expense Type", "Test Pay Expense"):
			frappe.get_doc({"doctype": "Expense Type", "expense_type_name": "Test Pay Expense"}).insert()

		if not frappe.db.exists("Project Configuration Profile", "Test Payroll Profile"):
			frappe.get_doc({
				"doctype": "Project Configuration Profile",
				"profile_name": "Test Payroll Profile",
				"max_overtime_hours_per_day": 4,
				"expense_range_rules": [
					{"expense_type": "Test Pay Expense", "min_amount": 100, "max_amount": 5000},
				],
			}).insert()

		self.worker = self._get_or_create_worker("Pay Test Worker", "Worker", 500, 100)
		self.supervisor = self._get_or_create_worker("Pay Test Supervisor", "Supervisor", 800, 150)

		if not frappe.db.exists("Project", {"project_name": "Test Pay Project"}):
			project = frappe.get_doc({
				"doctype": "Project",
				"project_name": "Test Pay Project",
				"start_date": "2026-01-01",
				"configuration_profile": "Test Payroll Profile",
				"project_budget": 500000,
				"worker_assignments": [
					{
						"worker": self.worker,
						"worker_name": "Pay Test Worker",
						"worker_type": "Worker",
						"daily_wage_rate": 500,
						"overtime_hourly_rate": 100,
						"is_active": 1,
					},
				],
			}).insert()
			self.project_name = project.name
		else:
			self.project_name = frappe.db.get_value("Project", {"project_name": "Test Pay Project"}, "name")

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

	def test_payroll_generation(self):
		"""Test payroll picks up attendance and computes correctly"""
		# Create attendance for March 1
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": "2026-03-01",
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Pay Test Worker",
					"status": "Present",
					"overtime_hours": 2,
				},
			],
		})
		att.insert()
		att.submit()

		# Create attendance for March 2
		att2 = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": "2026-03-02",
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Pay Test Worker",
					"status": "Half Day",
					"overtime_hours": 0,
				},
			],
		})
		att2.insert()
		att2.submit()

		# Generate payroll
		payroll = frappe.get_doc({
			"doctype": "Payroll Entry",
			"project": self.project_name,
			"payroll_month": "March",
			"payroll_year": 2026,
		})
		payroll.insert()
		payroll.generate_payroll()

		self.assertEqual(len(payroll.payroll_details), 1)

		detail = payroll.payroll_details[0]
		self.assertEqual(detail.total_present_days, 1.5)  # 1 full + 0.5 half
		self.assertEqual(detail.total_overtime_hours, 2)
		self.assertEqual(detail.gross_wage, 750)  # 500 * 1.5
		self.assertEqual(detail.overtime_amount, 200)  # 100 * 2
		self.assertEqual(detail.gross_pay, 950)

	def test_advance_recovery_on_submit(self):
		"""Test that advances are recovered when payroll is submitted"""
		# Create and submit an advance
		adv = frappe.get_doc({
			"doctype": "Worker Advance",
			"project": self.project_name,
			"worker": self.worker,
			"advance_date": "2026-04-05",
			"amount": 300,
			"given_by": self._get_or_create_worker("Pay Test Supervisor", "Supervisor", 800, 150),
			"payment_mode": "Cash",
		})
		adv.insert()
		adv.submit()

		# Create attendance for April 10
		att = frappe.get_doc({
			"doctype": "Daily Attendance",
			"project": self.project_name,
			"attendance_date": "2026-04-10",
			"attendance_details": [
				{
					"worker": self.worker,
					"worker_name": "Pay Test Worker",
					"status": "Present",
					"overtime_hours": 0,
				},
			],
		})
		att.insert()
		att.submit()

		# Generate and submit payroll for April (avoids conflict with March test)
		payroll = frappe.get_doc({
			"doctype": "Payroll Entry",
			"project": self.project_name,
			"payroll_month": "April",
			"payroll_year": 2026,
		})
		payroll.insert()
		payroll.generate_payroll()
		payroll.submit()

		# Check advance is recovered
		adv.reload()
		self.assertEqual(adv.recovery_status, "Fully Recovered")
		self.assertEqual(adv.recovered_amount, 300)

	def test_duplicate_payroll_blocked(self):
		"""Cannot create two payrolls for same project/month/year"""
		payroll1 = frappe.get_doc({
			"doctype": "Payroll Entry",
			"project": self.project_name,
			"payroll_month": "February",
			"payroll_year": 2026,
		})
		payroll1.insert()

		payroll2 = frappe.get_doc({
			"doctype": "Payroll Entry",
			"project": self.project_name,
			"payroll_month": "February",
			"payroll_year": 2026,
		})
		self.assertRaises(frappe.ValidationError, payroll2.insert)
