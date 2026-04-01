# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, today


class ExpenseEntry(Document):
	def validate(self):
		self.validate_expense_date()

	def validate_expense_date(self):
		if getdate(self.expense_date) > getdate(today()):
			frappe.msgprint(
				"Expense date is in the future. This will be flagged for review.",
				indicator="orange",
			)

	def on_submit(self):
		self.set_bill_from_attachments()
		self.run_auto_approval()
		if self.approval_status in ("Auto Approved", "Manually Approved"):
			self.update_project_expense_cost()
		if self.from_supervisor_fund:
			self.update_supervisor_fund("add")

	def set_bill_from_attachments(self):
		"""Auto-populate bill_attachment from sidebar attachments if field is empty."""
		if self.bill_attachment:
			return
		file_url = frappe.db.get_value(
			"File",
			{"attached_to_doctype": self.doctype, "attached_to_name": self.name},
			"file_url",
			order_by="creation desc",
		)
		if file_url:
			self.bill_attachment = file_url
			self.db_set("bill_attachment", file_url, update_modified=False)

	def on_cancel(self):
		if self.approval_status in ("Auto Approved", "Manually Approved"):
			self.reverse_project_expense_cost()
		if self.from_supervisor_fund:
			self.update_supervisor_fund("subtract")

	def run_auto_approval(self):
		project = frappe.get_doc("Project", self.project)
		profile = frappe.get_doc(
			"Project Configuration Profile", project.configuration_profile
		)

		flag_reasons = []

		# 1. Find matching expense range rule
		matching_rule = None
		for rule in profile.expense_range_rules:
			if rule.expense_type == self.expense_type:
				matching_rule = rule
				break

		if not matching_rule:
			flag_reasons.append(
				f"No range rule defined for expense type '{self.expense_type}'"
			)
		else:
			# 2. Check amount range
			if not (
				flt(matching_rule.min_amount)
				<= flt(self.amount)
				<= flt(matching_rule.max_amount)
			):
				flag_reasons.append(
					f"Amount {self.amount} outside range "
					f"[{matching_rule.min_amount}, {matching_rule.max_amount}]"
				)

			# 3. Check bill attachment requirement
			if matching_rule.requires_bill:
				has_bill = self.bill_attachment or frappe.db.exists(
					"File",
					{"attached_to_doctype": "Expense Entry", "attached_to_name": self.name},
				)
				if not has_bill:
					flag_reasons.append("Bill attachment required but not provided")

		# 4. Check date validity
		cutoff_days = project.expense_cutoff_days or 3
		days_diff = date_diff(self.posting_date, self.expense_date)

		if days_diff > cutoff_days:
			flag_reasons.append(
				f"Expense submitted {days_diff} days late (cutoff: {cutoff_days} days)"
			)

		if getdate(self.expense_date) < getdate(project.start_date):
			flag_reasons.append("Expense date is before project start date")

		if getdate(self.expense_date) > getdate(today()):
			flag_reasons.append("Expense date is in the future (pre-dated)")

		# Preserve flag if already set (e.g. edited expense)
		if self.is_flagged and self.flag_reason:
			flag_reasons.insert(0, self.flag_reason)

		# Decision
		if flag_reasons:
			self.is_flagged = 1
			self.flag_reason = "\n".join(flag_reasons)
			self.approval_status = "Pending Approval"
		else:
			self.is_flagged = 0
			self.flag_reason = ""
			self.approval_status = "Auto Approved"
			self.approved_on = today()

		self.db_set("approval_status", self.approval_status, update_modified=False)
		self.db_set("is_flagged", self.is_flagged, update_modified=False)
		self.db_set("flag_reason", self.flag_reason, update_modified=False)
		if self.approved_on:
			self.db_set("approved_on", self.approved_on, update_modified=False)

	def update_project_expense_cost(self):
		project = frappe.get_doc("Project", self.project)
		project.total_expense_cost = flt(project.total_expense_cost) + flt(self.amount)
		project.save(ignore_permissions=True)

		from refractec.refractec.utils import check_budget_alerts

		check_budget_alerts(self.project)

	def reverse_project_expense_cost(self):
		project = frappe.get_doc("Project", self.project)
		project.total_expense_cost = flt(project.total_expense_cost) - flt(self.amount)
		project.save(ignore_permissions=True)

	def update_supervisor_fund(self, action):
		"""Update project's supervisor fund tracking on expense submit/cancel."""
		project = frappe.get_doc("Project", self.project)
		sign = 1 if action == "add" else -1
		mode = getattr(self, "payment_mode", "Cash") or "Cash"

		project.fund_cash_out = flt(project.fund_cash_out)
		project.fund_bank_out = flt(project.fund_bank_out)

		if mode == "Cash":
			project.fund_cash_out += sign * flt(self.amount)
		else:
			project.fund_bank_out += sign * flt(self.amount)

		project.save(ignore_permissions=True)


@frappe.whitelist()
def approve_expense(name, remarks=None):
	"""Manually approve a flagged expense entry"""
	doc = frappe.get_doc("Expense Entry", name)
	if doc.approval_status != "Pending Approval":
		frappe.throw("Only expenses with 'Pending Approval' status can be approved")

	doc.approval_status = "Manually Approved"
	doc.approved_by = frappe.session.user
	doc.approved_on = today()
	doc.approval_remarks = remarks or ""
	doc.db_set("approval_status", doc.approval_status, update_modified=False)
	doc.db_set("approved_by", doc.approved_by, update_modified=False)
	doc.db_set("approved_on", doc.approved_on, update_modified=False)
	doc.db_set("approval_remarks", doc.approval_remarks, update_modified=False)

	doc.update_project_expense_cost()
	frappe.msgprint(f"Expense {name} has been approved.", indicator="green")


@frappe.whitelist()
def reject_expense(name, remarks=None):
	"""Reject a flagged expense entry"""
	doc = frappe.get_doc("Expense Entry", name)
	if doc.approval_status != "Pending Approval":
		frappe.throw("Only expenses with 'Pending Approval' status can be rejected")

	doc.approval_status = "Rejected"
	doc.approved_by = frappe.session.user
	doc.approved_on = today()
	doc.approval_remarks = remarks or ""
	doc.db_set("approval_status", doc.approval_status, update_modified=False)
	doc.db_set("approved_by", doc.approved_by, update_modified=False)
	doc.db_set("approved_on", doc.approved_on, update_modified=False)
	doc.db_set("approval_remarks", doc.approval_remarks, update_modified=False)

	frappe.msgprint(f"Expense {name} has been rejected.", indicator="red")


def get_permission_query_conditions(user):
	if not user:
		user = frappe.session.user

	if "Refractec Admin" in frappe.get_roles(user):
		return ""

	return """(`tabExpense Entry`.project in (
		select `for_value` from `tabUser Permission`
		where `user`={user} and `allow`='Project'
	))""".format(user=frappe.db.escape(user))


def has_permission(doc, ptype, user):
	if "Refractec Admin" in frappe.get_roles(user):
		return True

	permitted_projects = frappe.get_all(
		"User Permission",
		filters={"user": user, "allow": "Project"},
		pluck="for_value",
	)
	return doc.project in permitted_projects
