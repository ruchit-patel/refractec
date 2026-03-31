# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import today


class TestWorkerAdvance(IntegrationTestCase):
	def setUp(self):
		self.setup_test_data()

	def setup_test_data(self):
		if not frappe.db.exists("Expense Type", "Test Adv Expense"):
			frappe.get_doc({"doctype": "Expense Type", "expense_type_name": "Test Adv Expense"}).insert()

		if not frappe.db.exists("Project Configuration Profile", "Test Advance Profile"):
			frappe.get_doc({
				"doctype": "Project Configuration Profile",
				"profile_name": "Test Advance Profile",
				"advance_monthly_limit_per_worker": 5000,
				"expense_range_rules": [
					{"expense_type": "Test Adv Expense", "min_amount": 100, "max_amount": 5000},
				],
			}).insert()

		self.worker = self._get_or_create_worker("Adv Test Worker", "Worker")
		self.supervisor = self._get_or_create_worker("Adv Test Supervisor", "Supervisor")

		if not frappe.db.exists("Project", {"project_name": "Test Adv Project"}):
			project = frappe.get_doc({
				"doctype": "Project",
				"project_name": "Test Adv Project",
				"start_date": "2026-01-01",
				"configuration_profile": "Test Advance Profile",
				"project_budget": 100000,
				"worker_assignments": [
					{
						"worker": self.worker,
						"worker_name": "Adv Test Worker",
						"worker_type": "Worker",
						"daily_wage_rate": 500,
						"overtime_hourly_rate": 100,
						"is_active": 1,
					},
					{
						"worker": self.supervisor,
						"worker_name": "Adv Test Supervisor",
						"worker_type": "Supervisor",
						"daily_wage_rate": 800,
						"overtime_hourly_rate": 150,
						"is_active": 1,
					},
				],
			}).insert()
			self.project_name = project.name
		else:
			self.project_name = frappe.db.get_value("Project", {"project_name": "Test Adv Project"}, "name")

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

	def test_advance_creates_ledger_entry(self):
		adv = frappe.get_doc({
			"doctype": "Worker Advance",
			"project": self.project_name,
			"worker": self.worker,
			"advance_date": today(),
			"amount": 1000,
			"given_by": self.supervisor,
			"payment_mode": "Cash",
		})
		adv.insert()
		adv.submit()

		# Check ledger entry created
		ledger = frappe.get_all(
			"Advance Ledger Entry",
			filters={"reference_name": adv.name, "transaction_type": "Advance Given"},
			fields=["amount", "running_balance"],
		)
		self.assertEqual(len(ledger), 1)
		self.assertEqual(ledger[0].amount, 1000)

	def test_non_supervisor_cannot_give(self):
		"""Only supervisors can give advances"""
		adv = frappe.get_doc({
			"doctype": "Worker Advance",
			"project": self.project_name,
			"worker": self.supervisor,
			"advance_date": today(),
			"amount": 500,
			"given_by": self.worker,  # worker, not supervisor
			"payment_mode": "Cash",
		})
		self.assertRaises(frappe.ValidationError, adv.insert)

	def test_monthly_limit(self):
		"""Monthly advance limit should be enforced"""
		# First advance: 3000
		adv1 = frappe.get_doc({
			"doctype": "Worker Advance",
			"project": self.project_name,
			"worker": self.worker,
			"advance_date": today(),
			"amount": 3000,
			"given_by": self.supervisor,
			"payment_mode": "Cash",
		})
		adv1.insert()
		adv1.submit()

		# Second advance: 3000 (total would be 6000, limit is 5000)
		adv2 = frappe.get_doc({
			"doctype": "Worker Advance",
			"project": self.project_name,
			"worker": self.worker,
			"advance_date": today(),
			"amount": 3000,
			"given_by": self.supervisor,
			"payment_mode": "Cash",
		})
		self.assertRaises(frappe.ValidationError, adv2.insert)
