frappe.pages["accounts_dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Accounts Dashboard"),
		single_column: true,
	});
};

frappe.pages["accounts_dashboard"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("accounts_dashboard.bundle.jsx").then(() => {
		frappe.accounts_dashboard = new frappe.ui.Accounts_Dashboard({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}
