frappe.pages["admin_dashboard"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Refractec Dashboard"),
		single_column: true,
	});
};

frappe.pages["admin_dashboard"].on_page_show = function (wrapper) {
	load_desk_page(wrapper);
};

function load_desk_page(wrapper) {
	let $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();

	frappe.require("admin_dashboard.bundle.jsx").then(() => {
		frappe.admin_dashboard = new frappe.ui.Admin_Dashboard({
			wrapper: $parent,
			page: wrapper.page,
		});
	});
}
