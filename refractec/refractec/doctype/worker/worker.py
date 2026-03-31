# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Worker(Document):
	def validate(self):
		if self.date_of_leaving and self.date_of_leaving < self.date_of_joining:
			frappe.throw("Date of Leaving cannot be before Date of Joining")

		if self.date_of_leaving and self.status != "Left":
			self.status = "Left"
