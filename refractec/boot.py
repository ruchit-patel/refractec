import frappe


def boot_session(bootinfo):
	"""Hide non-Refractec desktop icons for users who only have Refractec roles."""
	refractec_roles = {"Refractec Admin", "Refractec Supervisor", "Refractec Accountant"}
	user_roles = set(frappe.get_roles())

	# If user has any Refractec role and no System Manager role,
	# show only the Refractec desktop icon
	if user_roles & refractec_roles and "System Manager" not in user_roles:
		bootinfo.desktop_icons = [
			icon for icon in bootinfo.get("desktop_icons", [])
			if icon.get("app") == "refractec" or icon.get("label") == "Refractec"
		]
