# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestWorker(IntegrationTestCase):
	def test_create_worker(self):
		worker = frappe.get_doc({
			"doctype": "Worker",
			"worker_name": "Test Worker",
			"worker_type": "Worker",
			"date_of_joining": "2026-01-01",
			"daily_wage_rate": 500,
			"overtime_hourly_rate": 100,
		})
		worker.insert()
		self.assertTrue(worker.name.startswith("WRK-"))
		self.assertEqual(worker.status, "Active")

	def test_create_supervisor(self):
		worker = frappe.get_doc({
			"doctype": "Worker",
			"worker_name": "Test Supervisor",
			"worker_type": "Supervisor",
			"date_of_joining": "2026-01-01",
			"daily_wage_rate": 800,
			"overtime_hourly_rate": 150,
		})
		worker.insert()
		self.assertEqual(worker.worker_type, "Supervisor")
