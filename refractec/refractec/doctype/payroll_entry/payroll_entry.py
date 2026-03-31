# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import calendar

import frappe
from frappe.model.document import Document
from frappe.utils import flt


MONTH_NAMES = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]


class PayrollEntry(Document):
	def validate(self):
		self.set_date_range()
		self.validate_duplicate_payroll()

	def set_date_range(self):
		month_number = MONTH_NAMES.index(self.payroll_month) + 1
		self.from_date = f"{self.payroll_year}-{month_number:02d}-01"
		last_day = calendar.monthrange(self.payroll_year, month_number)[1]
		self.to_date = f"{self.payroll_year}-{month_number:02d}-{last_day:02d}"

	def validate_duplicate_payroll(self):
		existing = frappe.db.exists("Payroll Entry", {
			"project": self.project,
			"payroll_month": self.payroll_month,
			"payroll_year": self.payroll_year,
			"docstatus": ["!=", 2],
			"name": ["!=", self.name],
		})
		if existing:
			frappe.throw(
				f"Payroll for {self.project} for {self.payroll_month} {self.payroll_year} "
				f"already exists: {existing}"
			)

	@frappe.whitelist()
	def generate_payroll(self):
		"""Pull attendance data and compute payroll for all assigned workers"""
		self.payroll_details = []

		project = frappe.get_doc("Project", self.project)
		workers = {
			row.worker: row
			for row in project.worker_assignments
			if row.is_active
		}

		for worker_id, assignment in workers.items():
			attendance_data = frappe.db.sql(
				"""
				SELECT
					SUM(CASE WHEN ad.status = 'Present' THEN 1
							 WHEN ad.status = 'Half Day' THEN 0.5
							 ELSE 0 END) as total_days,
					SUM(COALESCE(ad.overtime_hours, 0)) as total_ot
				FROM `tabAttendance Detail` ad
				JOIN `tabDaily Attendance` da ON da.name = ad.parent
				WHERE da.project = %s
				  AND da.attendance_date BETWEEN %s AND %s
				  AND da.docstatus = 1
				  AND ad.worker = %s
			""",
				(self.project, self.from_date, self.to_date, worker_id),
				as_dict=True,
			)[0]

			total_days = flt(attendance_data.total_days)
			total_ot = flt(attendance_data.total_ot)

			if total_days == 0 and total_ot == 0:
				continue

			daily_rate = flt(assignment.daily_wage_rate)
			ot_rate = flt(assignment.overtime_hourly_rate)

			gross_wage = daily_rate * total_days
			ot_amount = ot_rate * total_ot
			gross_pay = gross_wage + ot_amount

			# Get unrecovered advances
			advance_total = flt(
				frappe.db.sql(
					"""
				SELECT COALESCE(SUM(amount - COALESCE(recovered_amount, 0)), 0)
				FROM `tabWorker Advance`
				WHERE project = %s AND worker = %s AND docstatus = 1
				  AND recovery_status != 'Fully Recovered'
			""",
					(self.project, worker_id),
				)[0][0]
			)

			# Cap deduction at gross_pay — remaining advance carries to next month
			advance_deduction = min(advance_total, gross_pay)
			net_pay = gross_pay - advance_deduction

			self.append("payroll_details", {
				"worker": worker_id,
				"worker_name": assignment.worker_name,
				"worker_type": assignment.worker_type,
				"daily_wage_rate": daily_rate,
				"overtime_hourly_rate": ot_rate,
				"total_present_days": total_days,
				"total_overtime_hours": total_ot,
				"gross_wage": gross_wage,
				"overtime_amount": ot_amount,
				"gross_pay": gross_pay,
				"advance_deduction": advance_deduction,
				"other_deductions": 0,
				"net_pay": net_pay,
			})

		self.total_gross_pay = sum(
			flt(r.gross_pay) for r in self.payroll_details
		)
		self.total_advance_deduction = sum(
			flt(r.advance_deduction) for r in self.payroll_details
		)
		self.total_net_pay = sum(flt(r.net_pay) for r in self.payroll_details)
		self.save()

		frappe.msgprint(
			f"Payroll generated with {len(self.payroll_details)} workers.",
			indicator="green",
		)

	def on_submit(self):
		self.recover_advances()

	def on_cancel(self):
		self.reverse_advance_recovery()

	def recover_advances(self):
		for row in self.payroll_details:
			if flt(row.advance_deduction) <= 0:
				continue

			remaining_to_recover = flt(row.advance_deduction)
			advances = frappe.get_all(
				"Worker Advance",
				filters={
					"project": self.project,
					"worker": row.worker,
					"docstatus": 1,
					"recovery_status": ["!=", "Fully Recovered"],
				},
				fields=["name", "amount", "recovered_amount"],
				order_by="advance_date asc",
			)

			for adv in advances:
				if remaining_to_recover <= 0:
					break
				unrecovered = flt(adv.amount) - flt(adv.recovered_amount)
				recover_now = min(unrecovered, remaining_to_recover)

				new_recovered = flt(adv.recovered_amount) + recover_now
				new_status = (
					"Fully Recovered"
					if new_recovered >= flt(adv.amount)
					else "Partially Recovered"
				)

				frappe.db.set_value("Worker Advance", adv.name, {
					"recovered_amount": new_recovered,
					"recovery_status": new_status,
					"payroll_entry": self.name,
				})

				remaining_to_recover -= recover_now

			# Create ledger entry for recovery
			if flt(row.advance_deduction) > 0:
				last_balance = self._get_last_balance(row.worker)
				frappe.get_doc({
					"doctype": "Advance Ledger Entry",
					"project": self.project,
					"worker": row.worker,
					"posting_date": self.to_date,
					"transaction_type": "Advance Recovered",
					"amount": flt(row.advance_deduction),
					"running_balance": flt(last_balance) - flt(row.advance_deduction),
					"reference_doctype": "Payroll Entry",
					"reference_name": self.name,
					"remarks": f"Recovered via Payroll {self.name}",
				}).insert(ignore_permissions=True)

		# Update project totals
		total_recovered = sum(
			flt(r.advance_deduction) for r in self.payroll_details
		)
		if total_recovered > 0:
			project = frappe.get_doc("Project", self.project)
			project.total_advance_recovered = flt(project.total_advance_recovered) + total_recovered
			project.save(ignore_permissions=True)

	def reverse_advance_recovery(self):
		"""Reverse advance recovery when payroll is cancelled"""
		for row in self.payroll_details:
			if flt(row.advance_deduction) <= 0:
				continue

			# Find advances that were recovered by this payroll
			advances = frappe.get_all(
				"Worker Advance",
				filters={
					"project": self.project,
					"worker": row.worker,
					"docstatus": 1,
					"payroll_entry": self.name,
				},
				fields=["name", "amount", "recovered_amount"],
			)

			for adv in advances:
				frappe.db.set_value("Worker Advance", adv.name, {
					"recovery_status": "Unrecovered",
					"recovered_amount": 0,
					"payroll_entry": "",
				})

	def _get_last_balance(self, worker):
		result = frappe.db.sql(
			"""
			SELECT running_balance FROM `tabAdvance Ledger Entry`
			WHERE project=%s AND worker=%s
			ORDER BY posting_date DESC, creation DESC LIMIT 1
		""",
			(self.project, worker),
		)
		return flt(result[0][0]) if result else 0
