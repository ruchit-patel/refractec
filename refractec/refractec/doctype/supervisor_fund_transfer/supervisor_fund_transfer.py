# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SupervisorFundTransfer(Document):
	def validate(self):
		self.validate_supervisor()

	def validate_supervisor(self):
		worker_type = frappe.db.get_value("Worker", self.supervisor, "worker_type")
		if worker_type != "Supervisor":
			frappe.throw(f"{self.supervisor_name} is not a Supervisor")

	def on_submit(self):
		self.update_project_fund("add")

	def on_cancel(self):
		self.update_project_fund("subtract")

	def update_project_fund(self, action):
		project = frappe.get_doc("Project", self.project)
		sign = 1 if action == "add" else -1

		project.total_fund_given = flt(project.total_fund_given) + sign * flt(self.amount)

		if self.payment_mode == "Cash":
			project.fund_cash_in = flt(project.fund_cash_in) + sign * flt(self.amount)
		else:
			project.fund_bank_in = flt(project.fund_bank_in) + sign * flt(self.amount)

		project.save(ignore_permissions=True)
