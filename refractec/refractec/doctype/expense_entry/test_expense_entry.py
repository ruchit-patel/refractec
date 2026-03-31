# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today, add_days


class TestExpenseEntry(IntegrationTestCase):
	def setUp(self):
		self.setup_test_data()

	def setup_test_data(self):
		# Expense Type
		if not frappe.db.exists("Expense Type", "Test Cement"):
			frappe.get_doc({"doctype": "Expense Type", "expense_type_name": "Test Cement"}).insert()

		if not frappe.db.exists("Expense Type", "Test Unknown"):
			frappe.get_doc({"doctype": "Expense Type", "expense_type_name": "Test Unknown"}).insert()

		# Profile with range rules
		if not frappe.db.exists("Project Configuration Profile", "Test Expense Profile"):
			frappe.get_doc({
				"doctype": "Project Configuration Profile",
				"profile_name": "Test Expense Profile",
				"expense_cutoff_days": 3,
				"expense_range_rules": [
					{
						"expense_type": "Test Cement",
						"min_amount": 500,
						"max_amount": 10000,
						"requires_bill": 1,
					},
				],
			}).insert()

		# Worker
		self.worker = self._get_or_create_worker("Exp Test Worker", "Worker")
		self.supervisor = self._get_or_create_worker("Exp Test Supervisor", "Supervisor")

		# Project
		if not frappe.db.exists("Project", {"project_name": "Test Exp Project"}):
			project = frappe.get_doc({
				"doctype": "Project",
				"project_name": "Test Exp Project",
				"start_date": "2026-01-01",
				"configuration_profile": "Test Expense Profile",
				"project_budget": 200000,
				"worker_assignments": [
					{
						"worker": self.worker,
						"worker_name": "Exp Test Worker",
						"worker_type": "Worker",
						"daily_wage_rate": 500,
						"overtime_hourly_rate": 100,
						"is_active": 1,
					},
				],
			}).insert()
			self.project_name = project.name
		else:
			self.project_name = frappe.db.get_value("Project", {"project_name": "Test Exp Project"}, "name")

	def _get_or_create_worker(self, name, worker_type):
		existing = frappe.db.get_value("Worker", {"worker_name": name}, "name")
		if existing:
			return existing
		w = frappe.get_doc({
			"doctype": "Worker",
			"worker_name": name,
			"worker_type": worker_type,
			"date_of_joining": "2026-01-01",
			"daily_wage_rate": 500,
			"overtime_hourly_rate": 100,
		}).insert()
		return w.name

	def test_auto_approval_within_range(self):
		"""Expense within range should be auto-approved"""
		expense = frappe.get_doc({
			"doctype": "Expense Entry",
			"project": self.project_name,
			"expense_type": "Test Cement",
			"expense_date": today(),
			"posting_date": today(),
			"amount": 2000,
			"submitted_by": self.worker,
			"bill_attachment": "/files/test_bill.pdf",
		})
		expense.insert()
		expense.submit()

		expense.reload()
		self.assertEqual(expense.approval_status, "Auto Approved")
		self.assertEqual(expense.is_flagged, 0)

	def test_flagged_out_of_range(self):
		"""Expense outside range should be flagged"""
		expense = frappe.get_doc({
			"doctype": "Expense Entry",
			"project": self.project_name,
			"expense_type": "Test Cement",
			"expense_date": today(),
			"posting_date": today(),
			"amount": 50000,  # exceeds max of 10000
			"submitted_by": self.worker,
			"bill_attachment": "/files/test_bill.pdf",
		})
		expense.insert()
		expense.submit()

		expense.reload()
		self.assertEqual(expense.approval_status, "Pending Approval")
		self.assertEqual(expense.is_flagged, 1)
		self.assertIn("outside range", expense.flag_reason)

	def test_flagged_missing_bill(self):
		"""Expense requiring bill but missing it should be flagged"""
		expense = frappe.get_doc({
			"doctype": "Expense Entry",
			"project": self.project_name,
			"expense_type": "Test Cement",
			"expense_date": today(),
			"posting_date": today(),
			"amount": 2000,
			"submitted_by": self.worker,
			# no bill_attachment
		})
		expense.insert()
		expense.submit()

		expense.reload()
		self.assertEqual(expense.approval_status, "Pending Approval")
		self.assertIn("Bill attachment required", expense.flag_reason)

	def test_flagged_late_submission(self):
		"""Expense submitted too late should be flagged"""
		expense = frappe.get_doc({
			"doctype": "Expense Entry",
			"project": self.project_name,
			"expense_type": "Test Cement",
			"expense_date": add_days(today(), -10),  # 10 days ago, cutoff is 3
			"posting_date": today(),
			"amount": 2000,
			"submitted_by": self.worker,
			"bill_attachment": "/files/test_bill.pdf",
		})
		expense.insert()
		expense.submit()

		expense.reload()
		self.assertEqual(expense.approval_status, "Pending Approval")
		self.assertIn("days late", expense.flag_reason)

	def test_flagged_no_range_rule(self):
		"""Expense with no matching range rule should be flagged"""
		expense = frappe.get_doc({
			"doctype": "Expense Entry",
			"project": self.project_name,
			"expense_type": "Test Unknown",  # no rule for this type
			"expense_date": today(),
			"posting_date": today(),
			"amount": 1000,
			"submitted_by": self.worker,
		})
		expense.insert()
		expense.submit()

		expense.reload()
		self.assertEqual(expense.approval_status, "Pending Approval")
		self.assertIn("No range rule", expense.flag_reason)
