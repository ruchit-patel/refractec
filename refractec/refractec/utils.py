# Copyright (c) 2026, Ruchit and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt


def check_budget_alerts(project_name):
	"""Check if budget thresholds are crossed and send alerts"""
	settings = frappe.get_single("Refractec Settings")
	if not settings.enable_budget_alerts:
		return

	project = frappe.get_doc("Project", project_name)
	utilization = flt(project.budget_utilization_pct)

	if utilization >= flt(settings.budget_critical_threshold):
		level = "Critical"
	elif utilization >= flt(settings.budget_warning_threshold):
		level = "Warning"
	else:
		return

	recipients = [
		r.user
		for r in settings.notification_email_recipients
		if r.notification_type in ("Budget Alert", "All")
	]

	if recipients:
		frappe.sendmail(
			recipients=recipients,
			subject=f"[{level}] Budget Alert: {project.project_name}",
			message=f"""
				<p><strong>Project:</strong> {project.project_name} ({project.name})</p>
				<p><strong>Budget:</strong> {project.project_budget}</p>
				<p><strong>Total Cost:</strong> {project.total_cost}</p>
				<p><strong>Utilization:</strong> {utilization:.1f}%</p>
				<p><strong>Level:</strong> {level}</p>
			""",
		)
