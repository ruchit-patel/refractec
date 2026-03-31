from frappe import _


def get_data():
	return {
		"fieldname": "project",
		"non_standard_fieldnames": {},
		"transactions": [
			{
				"label": _("Attendance"),
				"items": ["Daily Attendance"],
			},
			{
				"label": _("Expenses"),
				"items": ["Expense Entry"],
			},
			{
				"label": _("Advances"),
				"items": ["Worker Advance"],
			},
			{
				"label": _("Payroll"),
				"items": ["Payroll Entry"],
			},
		],
	}
