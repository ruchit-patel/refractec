import * as React from "react";
import { App } from "./App";
import { createRoot } from "react-dom/client";

class Admin_Dashboard {
	constructor({ page, wrapper }) {
		this.$wrapper = $(wrapper);
		this.page = page;
		this.init();
	}

	init() {
		this.setup_page_actions();
		this.setup_app();
	}

	setup_page_actions() {
		this.page.set_primary_action(__("Refresh"), () => {
			if (this.$admin_dashboard && this._refreshFn) {
				this._refreshFn();
			}
		}, "refresh");
	}

	setup_app() {
		const root = createRoot(this.$wrapper.get(0));
		root.render(<App onRefreshRef={(fn) => { this._refreshFn = fn; }} />);
		this.$admin_dashboard = root;
	}
}

frappe.provide("frappe.ui");
frappe.ui.Admin_Dashboard = Admin_Dashboard;
export default Admin_Dashboard;
