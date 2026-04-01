# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SupervisorFundTransfer(Document):
	def validate(self):
		if flt(self.amount) <= 0:
			frappe.throw("Amount must be greater than zero")
		self.validate_supervisor()
		self.validate_inter_project()
		if self.transfer_type in ("Fund Returned", "Inter-Project Transfer"):
			self.validate_fund_availability()

	def validate_supervisor(self):
		worker_type = frappe.db.get_value("Worker", self.supervisor, "worker_type")
		if worker_type != "Supervisor":
			frappe.throw(f"{self.supervisor_name} is not a Supervisor")

	def validate_inter_project(self):
		if self.transfer_type == "Inter-Project Transfer":
			if not self.to_project:
				frappe.throw("To Project is required for Inter-Project Transfer")
			if self.to_project == self.project:
				frappe.throw("From Project and To Project cannot be the same")

	def validate_fund_availability(self):
		"""Check if the return/transfer amount is available.
		If selected mode doesn't have enough, check if other mode covers shortfall
		(implies supervisor converted cash↔bank).
		"""
		project = frappe.get_doc("Project", self.project)
		amount = flt(self.amount)
		cash_bal = flt(project.fund_cash_balance)
		bank_bal = flt(project.fund_bank_balance)
		total_bal = cash_bal + bank_bal

		if amount > total_bal:
			frappe.throw(
				f"Insufficient fund balance. "
				f"Total available: ₹{total_bal:,.2f} "
				f"(Cash: ₹{cash_bal:,.2f}, Bank: ₹{bank_bal:,.2f})"
			)

		if self.payment_mode == "Cash":
			mode_bal = cash_bal
			other_mode = "Bank"
			other_bal = bank_bal
		else:
			mode_bal = bank_bal
			other_mode = "Cash"
			other_bal = cash_bal

		if amount > mode_bal and mode_bal >= 0:
			shortfall = amount - mode_bal
			if shortfall <= other_bal:
				# Other mode covers shortfall — this is a conversion
				frappe.msgprint(
					f"₹{shortfall:,.2f} will be adjusted from {other_mode} balance "
					f"(supervisor converted {other_mode.lower()} to {self.payment_mode.lower()}).",
					indicator="orange",
					alert=True,
				)
			else:
				frappe.throw(
					f"Insufficient {self.payment_mode} balance (₹{mode_bal:,.2f}). "
					f"{other_mode} balance (₹{other_bal:,.2f}) also cannot cover the shortfall."
				)

	def on_submit(self):
		if self.transfer_type == "Fund Given":
			self._credit_fund(self.project)
		elif self.transfer_type == "Fund Returned":
			self._debit_fund_with_conversion(self.project)
		elif self.transfer_type == "Inter-Project Transfer":
			self._debit_fund_with_conversion(self.project)
			self._credit_fund(self.to_project)

	def on_cancel(self):
		if self.transfer_type == "Fund Given":
			self._reverse_credit(self.project)
		elif self.transfer_type == "Fund Returned":
			self._reverse_debit(self.project)
		elif self.transfer_type == "Inter-Project Transfer":
			self._reverse_debit(self.project)
			self._reverse_credit(self.to_project)

	def _credit_fund(self, project_name):
		"""Add money to a project's supervisor fund."""
		project = frappe.get_doc("Project", project_name)
		project.total_fund_given = flt(project.total_fund_given) + flt(self.amount)

		if self.payment_mode == "Cash":
			project.fund_cash_in = flt(project.fund_cash_in) + flt(self.amount)
		else:
			project.fund_bank_in = flt(project.fund_bank_in) + flt(self.amount)

		project.save(ignore_permissions=True)

	def _debit_fund_with_conversion(self, project_name):
		"""Remove money from fund. If selected mode doesn't have enough,
		debit the shortfall from the other mode (cash↔bank conversion).
		"""
		project = frappe.get_doc("Project", project_name)
		amount = flt(self.amount)

		if self.payment_mode == "Cash":
			cash_available = flt(project.fund_cash_balance)
			if amount <= cash_available:
				# Enough in cash
				project.fund_cash_in = flt(project.fund_cash_in) - amount
			else:
				# Take what's in cash, rest from bank
				shortfall = amount - cash_available
				project.fund_cash_in = flt(project.fund_cash_in) - cash_available
				project.fund_bank_in = flt(project.fund_bank_in) - shortfall
		else:
			bank_available = flt(project.fund_bank_balance)
			if amount <= bank_available:
				project.fund_bank_in = flt(project.fund_bank_in) - amount
			else:
				shortfall = amount - bank_available
				project.fund_bank_in = flt(project.fund_bank_in) - bank_available
				project.fund_cash_in = flt(project.fund_cash_in) - shortfall

		project.total_fund_given = flt(project.total_fund_given) - amount
		project.save(ignore_permissions=True)

	def _reverse_credit(self, project_name):
		"""Reverse a credit (for cancellation of Fund Given)."""
		project = frappe.get_doc("Project", project_name)
		project.total_fund_given = flt(project.total_fund_given) - flt(self.amount)

		if self.payment_mode == "Cash":
			project.fund_cash_in = flt(project.fund_cash_in) - flt(self.amount)
		else:
			project.fund_bank_in = flt(project.fund_bank_in) - flt(self.amount)

		project.save(ignore_permissions=True)

	def _reverse_debit(self, project_name):
		"""Reverse a debit (for cancellation of Fund Returned / Inter-Project).
		Simply re-credits the full amount back to the selected mode.
		"""
		project = frappe.get_doc("Project", project_name)
		project.total_fund_given = flt(project.total_fund_given) + flt(self.amount)

		if self.payment_mode == "Cash":
			project.fund_cash_in = flt(project.fund_cash_in) + flt(self.amount)
		else:
			project.fund_bank_in = flt(project.fund_bank_in) + flt(self.amount)

		project.save(ignore_permissions=True)
