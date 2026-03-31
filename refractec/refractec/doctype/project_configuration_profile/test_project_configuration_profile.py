# Copyright (c) 2026, Ruchit and Contributors
# See license.txt

import frappe
from frappe.tests import IntegrationTestCase


class TestProjectConfigurationProfile(IntegrationTestCase):
	def test_create_profile(self):
		profile = frappe.get_doc({
			"doctype": "Project Configuration Profile",
			"profile_name": "Test Profile",
			"max_overtime_hours_per_day": 4,
			"expense_cutoff_days": 3,
			"expense_range_rules": [
				{
					"expense_type": self._get_expense_type(),
					"min_amount": 100,
					"max_amount": 5000,
					"requires_bill": 1,
				}
			],
		})
		profile.insert()
		self.assertEqual(profile.name, "Test Profile")
		self.assertEqual(len(profile.expense_range_rules), 1)

	def test_duplicate_expense_type_in_rules(self):
		et = self._get_expense_type()
		profile = frappe.get_doc({
			"doctype": "Project Configuration Profile",
			"profile_name": "Test Duplicate Rules",
			"expense_range_rules": [
				{"expense_type": et, "min_amount": 100, "max_amount": 5000},
				{"expense_type": et, "min_amount": 200, "max_amount": 6000},
			],
		})
		self.assertRaises(frappe.ValidationError, profile.insert)

	def test_min_greater_than_max(self):
		profile = frappe.get_doc({
			"doctype": "Project Configuration Profile",
			"profile_name": "Test Min Max",
			"expense_range_rules": [
				{
					"expense_type": self._get_expense_type(),
					"min_amount": 5000,
					"max_amount": 100,
				}
			],
		})
		self.assertRaises(frappe.ValidationError, profile.insert)

	def _get_expense_type(self):
		if not frappe.db.exists("Expense Type", "Test Expense"):
			frappe.get_doc({
				"doctype": "Expense Type",
				"expense_type_name": "Test Expense",
			}).insert()
		return "Test Expense"
