# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate, today, date_diff


class ProjectDeposit(Document):
	def validate(self):
		self.validate_dates()
		self.update_status()

	def validate_dates(self):
		if self.due_date and self.deposit_date:
			if getdate(self.due_date) < getdate(self.deposit_date):
				frappe.throw("Expected Collection Date cannot be before Deposit Date")

	def update_status(self):
		"""Auto-update status based on collection and due date."""
		collected = flt(self.collected_amount)
		amount = flt(self.amount)

		if self.status == "Forfeited":
			return

		if collected >= amount and collected > 0:
			self.status = "Collected"
			self.days_overdue = 0
		elif collected > 0 and collected < amount:
			self.status = "Partially Collected"
			if getdate(self.due_date) < getdate(today()):
				self.days_overdue = date_diff(today(), self.due_date)
			else:
				self.days_overdue = 0
		elif getdate(self.due_date) < getdate(today()):
			self.status = "Overdue"
			self.days_overdue = date_diff(today(), self.due_date)
		else:
			self.status = "Pending"
			self.days_overdue = 0
