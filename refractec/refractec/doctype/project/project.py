# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class Project(Document):
	def validate(self):
		self.validate_dates()
		self.validate_duplicate_workers()
		self.compute_budget_totals()

	def validate_dates(self):
		if self.expected_end_date and self.expected_end_date < self.start_date:
			frappe.throw("Expected End Date cannot be before Start Date")
		if self.actual_end_date and self.actual_end_date < self.start_date:
			frappe.throw("Actual End Date cannot be before Start Date")

	def validate_duplicate_workers(self):
		seen = set()
		for row in self.worker_assignments:
			if row.worker in seen:
				frappe.throw(f"Worker {row.worker} ({row.worker_name}) is assigned more than once")
			seen.add(row.worker)

	def compute_budget_totals(self):
		for item in self.budget_items:
			item.remaining_amount = flt(item.allocated_amount) - flt(item.spent_amount)

		self.total_cost = flt(self.total_labor_cost) + flt(self.total_expense_cost)
		self.budget_variance = flt(self.project_budget) - flt(self.total_cost)
		if flt(self.project_budget):
			self.budget_utilization_pct = (flt(self.total_cost) / flt(self.project_budget)) * 100
		else:
			self.budget_utilization_pct = 0
