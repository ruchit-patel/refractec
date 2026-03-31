# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ProjectConfigurationProfile(Document):
	def validate(self):
		self.validate_range_rules()

	def validate_range_rules(self):
		seen = set()
		for rule in self.expense_range_rules:
			if rule.expense_type in seen:
				frappe.throw(
					f"Duplicate expense type '{rule.expense_type}' in range rules"
				)
			seen.add(rule.expense_type)

			if rule.min_amount > rule.max_amount:
				frappe.throw(
					f"Min Amount cannot be greater than Max Amount for '{rule.expense_type}'"
				)
