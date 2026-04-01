# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SalarySlip(Document):
	def validate(self):
		self.set_employee_name()
		self.recalculate()

	def set_employee_name(self):
		"""Auto-set employee_name from worker if linked."""
		if self.worker and not self.employee_name:
			self.employee_name = frappe.db.get_value("Worker", self.worker, "worker_name")
		if not self.employee_name and not self.worker:
			frappe.throw("Please enter Employee Name or select a Worker")

	def recalculate(self):
		"""Recalculate all computed totals."""
		self.total_earnings = sum(flt(r.amount) for r in (self.slip_earnings or []))
		self.total_deductions = sum(flt(r.amount) for r in (self.slip_deductions or []))

		self.gross_pay = flt(self.gross_wage) + flt(self.overtime_amount) + flt(self.total_earnings)
		self.total_all_deductions = (
			flt(self.advance_deduction)
			+ flt(self.total_deductions)
			+ flt(self.other_deductions)
		)
		self.net_pay = flt(self.gross_pay) - flt(self.total_all_deductions)
