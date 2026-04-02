import * as React from "react";
const { useState, useEffect, useCallback } = React;

/* ─── colour palette (shared with admin dashboard) ─── */
const C = {
	primary: "#2563eb", primaryLight: "#dbeafe", primaryBg: "#eff6ff",
	success: "#16a34a", successLight: "#dcfce7",
	danger: "#dc2626", dangerLight: "#fee2e2",
	warning: "#f59e0b", warningLight: "#fef3c7",
	info: "#3b82f6", infoLight: "#dbeafe",
	purple: "#7c3aed", purpleLight: "#ede9fe",
	gray50: "#f8fafc", gray100: "#f1f5f9", gray200: "#e2e8f0",
	gray300: "#cbd5e1", gray400: "#94a3b8", gray500: "#64748b",
	gray600: "#475569", gray700: "#334155", gray800: "#1e293b",
	gray900: "#0f172a", white: "#ffffff",
};

const CHART_COLORS = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a", "#0891b2", "#4f46e5", "#059669"];

const fmt = (n) => {
	if (n == null) return "\u20B90";
	if (n >= 100000) return `\u20B9${(n / 100000).toFixed(1)}L`;
	if (n >= 1000) return `\u20B9${(n / 1000).toFixed(1)}K`;
	return `\u20B9${Number(n).toLocaleString("en-IN")}`;
};
const fmtFull = (n) => `\u20B9${Number(n || 0).toLocaleString("en-IN")}`;
const pct = (a, b) => b > 0 ? `${((a / b) * 100).toFixed(0)}%` : "0%";

/* ─── Main App ─── */
export function App({ onRefreshRef }) {
	const [data, setData] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [approvalCollapsed, setApprovalCollapsed] = useState(false);

	const fetchData = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const r = await frappe.call({ method: "refractec.api.get_accountant_dashboard_data" });
			setData(r.message);
		} catch (e) {
			setError(e?.message || "Failed to load dashboard data");
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => { fetchData(); }, [fetchData]);
	useEffect(() => { if (onRefreshRef) onRefreshRef(fetchData); }, [onRefreshRef, fetchData]);

	if (loading) return <Loading />;
	if (error) return <Error message={error} onRetry={fetchData} />;
	if (!data) return null;

	return (
		<div style={{ background: C.gray50, minHeight: "100vh", padding: "24px 32px" }}>
			<SummaryCards summary={data.summary} />

			{/* Approval Queue */}
			<ApprovalQueue
				expenses={data.pending_expenses}
				collapsed={approvalCollapsed}
				onToggle={() => setApprovalCollapsed(!approvalCollapsed)}
				onAction={fetchData}
			/>

			{/* Main grid */}
			<div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 24, marginTop: 24 }}>
				<div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
					<PayrollStatus entries={data.payroll_status} month={data.payroll_month} />
					<AdvanceRecovery workers={data.advance_by_worker} />
				</div>
				<div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
					<ExpenseByType data={data.expense_by_type} />
					{data.deposits.length > 0 && <DepositTracker deposits={data.deposits} />}
					<RecentActivity approved={data.recent_approved} payrolls={data.recent_payrolls} />
				</div>
			</div>

			{/* Cashflow Chart */}
			<CashflowChart chart={data.cashflow_chart} />

			{/* Quick Reports */}
			<QuickReports />
		</div>
	);
}

/* ─── Loading / Error ─── */
function Loading() {
	return (
		<div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300 }}>
			<div style={{ fontSize: 14, color: C.gray500 }}>Loading dashboard...</div>
		</div>
	);
}

function Error({ message, onRetry }) {
	return (
		<div style={{ textAlign: "center", padding: 60 }}>
			<div style={{ fontSize: 40, marginBottom: 12 }}>!</div>
			<p style={{ color: C.gray600, marginBottom: 16 }}>{message}</p>
			<button onClick={onRetry} style={{ ...btnStyle, background: C.primary, color: C.white }}>Retry</button>
		</div>
	);
}

/* ─── Summary Cards ─── */
function SummaryCards({ summary }) {
	const cards = [
		{ label: "Pending Approvals", value: summary.pending_approvals, icon: "alert-circle", color: summary.pending_approvals > 0 ? C.danger : C.success, route: "/app/expense-entry?approval_status=Pending+Approval" },
		{ label: "Flagged Expenses", value: summary.flagged_expenses, icon: "flag", color: summary.flagged_expenses > 0 ? C.warning : C.success, route: "/app/expense-entry?is_flagged=1&approval_status=Pending+Approval" },
		{ label: "Payroll This Month", value: fmt(summary.payroll_this_month), icon: "credit-card", color: C.primary, route: "/app/payroll-entry" },
		{ label: "Expenses This Month", value: fmt(summary.total_expenses_month), icon: "file-text", color: C.info, route: "/app/expense-entry" },
		{ label: "Advances Outstanding", value: fmt(summary.outstanding_advances), icon: "dollar-sign", color: summary.outstanding_advances > 0 ? C.warning : C.success, route: "/app/worker-advance?recovery_status=%5B%22in%22%2C%5B%22Unrecovered%22%2C%22Partially+Recovered%22%5D%5D" },
		{ label: "Total Advances Given", value: fmt(summary.total_advances_given), icon: "trending-up", color: C.purple, route: "/app/worker-advance" },
	];

	return (
		<div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 16, marginBottom: 24 }}>
			{cards.map((c, i) => (
				<a key={i} href={c.route} style={{ ...cardStyle, textDecoration: "none", cursor: "pointer", transition: "box-shadow 0.15s" }}>
					<div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
						<div style={{
							width: 36, height: 36, borderRadius: 8,
							background: c.color + "15", display: "flex",
							alignItems: "center", justifyContent: "center",
						}}>
							<FeatherIcon name={c.icon} size={18} color={c.color} />
						</div>
					</div>
					<div style={{ fontSize: 22, fontWeight: 700, color: C.gray900 }}>{c.value}</div>
					<div style={{ fontSize: 12, color: C.gray500, marginTop: 2 }}>{c.label}</div>
				</a>
			))}
		</div>
	);
}

/* ─── Approval Queue ─── */
function ApprovalQueue({ expenses, collapsed, onToggle, onAction }) {
	const [processing, setProcessing] = useState(null);

	const handleAction = (name, action) => {
		const title = action === "approve" ? "Approve Expense" : "Reject Expense";
		const reqd = action === "reject" ? 1 : 0;

		frappe.prompt(
			[{
				fieldname: "remarks",
				label: "Remarks",
				fieldtype: "Small Text",
				reqd,
				description: action === "reject" ? "Reason for rejection is required" : "Optional remarks",
			}],
			async (values) => {
				setProcessing(name);
				try {
					await frappe.call({
						method: `refractec.refractec.doctype.expense_entry.expense_entry.${action}_expense`,
						args: { name, remarks: values.remarks || "" },
					});
					frappe.show_alert({ message: `Expense ${action}d`, indicator: action === "approve" ? "green" : "red" });
					onAction();
				} catch (e) {
					frappe.show_alert({ message: e?.message || "Action failed", indicator: "red" });
				} finally {
					setProcessing(null);
				}
			},
			title,
			action === "approve" ? "Approve" : "Reject"
		);
	};

	return (
		<div style={cardStyle}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: collapsed ? 0 : 16 }}>
				<h3 style={sectionTitle}>
					Expense Approval Queue
					{expenses.length > 0 && (
						<span style={{
							marginLeft: 8, fontSize: 12, fontWeight: 600, padding: "2px 10px",
							borderRadius: 20, background: C.dangerLight, color: C.danger,
						}}>{expenses.length}</span>
					)}
				</h3>
				<button onClick={onToggle} style={{ ...linkBtn, fontSize: 13 }}>
					{collapsed ? "Expand" : "Collapse"}
				</button>
			</div>

			{!collapsed && expenses.length === 0 && (
				<div style={{ textAlign: "center", padding: "20px 0", color: C.gray400 }}>
					All caught up! No pending approvals.
				</div>
			)}

			{!collapsed && expenses.length > 0 && (
				<div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
					{expenses.map((e) => (
						<div key={e.name} style={{
							background: e.is_flagged ? C.warningLight : C.gray50,
							borderLeft: `4px solid ${e.is_flagged ? C.warning : C.info}`,
							borderRadius: 8, padding: "12px 16px",
						}}>
							<div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
								<div style={{ flex: 1 }}>
									<div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
										<span style={{ fontWeight: 600, fontSize: 13, color: C.gray800 }}>{e.expense_type_name}</span>
										<span style={{ fontSize: 16, fontWeight: 700, color: C.gray900 }}>{fmtFull(e.amount)}</span>
										{e.is_flagged ? (
											<span style={{ fontSize: 10, fontWeight: 600, padding: "1px 8px", borderRadius: 10, background: C.warning + "30", color: C.warning }}>FLAGGED</span>
										) : null}
									</div>
									<div style={{ fontSize: 12, color: C.gray500, marginTop: 4 }}>
										{e.submitted_by_name} {"\u00B7"} {e.project_name} {"\u00B7"} {frappe.datetime.str_to_user(e.expense_date)}
									</div>
									{e.flag_reason && (
										<div style={{ fontSize: 11, color: C.warning, marginTop: 4, fontStyle: "italic" }}>{e.flag_reason}</div>
									)}
									{e.description && (
										<div style={{ fontSize: 12, color: C.gray600, marginTop: 4 }}>{e.description}</div>
									)}
								</div>
								<div style={{ display: "flex", gap: 8, marginLeft: 12, flexShrink: 0 }}>
									{e.bill_attachment && (
										<a href={e.bill_attachment} target="_blank" rel="noreferrer"
											style={{ ...smallBtn, background: C.gray200, color: C.gray700 }}>
											Bill
										</a>
									)}
									<a href={`/app/expense-entry/${e.name}`}
										style={{ ...smallBtn, background: C.gray200, color: C.gray700 }}>
										Open
									</a>
									<button
										onClick={() => handleAction(e.name, "approve")}
										disabled={processing === e.name}
										style={{ ...smallBtn, background: C.success, color: C.white }}
									>
										{processing === e.name ? "..." : "Approve"}
									</button>
									<button
										onClick={() => handleAction(e.name, "reject")}
										disabled={processing === e.name}
										style={{ ...smallBtn, background: C.danger, color: C.white }}
									>
										Reject
									</button>
								</div>
							</div>
						</div>
					))}
				</div>
			)}
		</div>
	);
}

/* ─── Payroll Status ─── */
function PayrollStatus({ entries, month }) {
	const statusColor = { "Submitted": C.success, "Draft": C.warning, "Not Created": C.gray400 };
	const statusBg = { "Submitted": C.successLight, "Draft": C.warningLight, "Not Created": C.gray100 };

	return (
		<div style={cardStyle}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
				<h3 style={sectionTitle}>Payroll Status &mdash; {month}</h3>
				<a href="/app/payroll-entry" style={linkBtn}>View All</a>
			</div>
			{entries.length === 0 && (
				<div style={{ color: C.gray400, fontSize: 13, textAlign: "center", padding: 16 }}>No active projects</div>
			)}
			{entries.map((e, i) => (
				<div key={i} style={{
					display: "flex", justifyContent: "space-between", alignItems: "center",
					padding: "12px 0", borderBottom: i < entries.length - 1 ? `1px solid ${C.gray100}` : "none",
					cursor: e.payroll_name ? "pointer" : "default",
				}} onClick={() => e.payroll_name && frappe.set_route("Form", "Payroll Entry", e.payroll_name)}>
					<div>
						<div style={{ fontWeight: 600, fontSize: 13, color: C.gray800 }}>{e.project_name}</div>
						<div style={{ fontSize: 12, color: C.gray500, marginTop: 2 }}>
							Gross: {fmtFull(e.gross_pay)} {"\u00B7"} Ded: {fmtFull(e.deductions)} {"\u00B7"} Net: {fmtFull(e.net_pay)}
						</div>
					</div>
					<span style={{
						fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 20,
						background: statusBg[e.status] || C.gray100,
						color: statusColor[e.status] || C.gray500,
					}}>{e.status}</span>
				</div>
			))}
		</div>
	);
}

/* ─── Advance Recovery ─── */
function AdvanceRecovery({ workers }) {
	if (!workers || workers.length === 0) {
		return (
			<div style={cardStyle}>
				<h3 style={{ ...sectionTitle, marginBottom: 14 }}>Advance Recovery Tracker</h3>
				<div style={{ color: C.gray400, fontSize: 13, textAlign: "center", padding: 16 }}>No outstanding advances</div>
			</div>
		);
	}

	return (
		<div style={cardStyle}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
				<h3 style={sectionTitle}>Advance Recovery Tracker</h3>
				<a href="/app/query-report/Worker Wise Advance Balance" style={linkBtn}>Full Report</a>
			</div>
			{workers.map((w, i) => {
				const recoveryPct = w.total_given > 0 ? (w.total_recovered / w.total_given) * 100 : 0;
				return (
					<div key={i} style={{ marginBottom: 14 }}>
						<div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
							<span style={{ color: C.gray700, fontWeight: 600 }}>{w.worker_name}</span>
							<span style={{ color: C.gray600 }}>
								{fmtFull(w.total_recovered)} / {fmtFull(w.total_given)}
								<span style={{ marginLeft: 6, fontWeight: 700, color: w.outstanding > 0 ? C.danger : C.success }}>
									({fmtFull(w.outstanding)} due)
								</span>
							</span>
						</div>
						<div style={{ height: 8, borderRadius: 4, background: C.gray200 }}>
							<div style={{
								height: 8, borderRadius: 4,
								width: `${Math.min(recoveryPct, 100)}%`,
								background: recoveryPct >= 100 ? C.success : recoveryPct >= 50 ? C.warning : C.danger,
								transition: "width 0.5s ease",
							}} />
						</div>
					</div>
				);
			})}
		</div>
	);
}

/* ─── Expense By Type (donut-style horizontal bars) ─── */
function ExpenseByType({ data }) {
	const total = data.reduce((s, d) => s + (d.value || 0), 0);

	return (
		<div style={cardStyle}>
			<h3 style={{ ...sectionTitle, marginBottom: 14 }}>Expenses by Type (This Month)</h3>
			{data.length === 0 && <div style={{ color: C.gray400, fontSize: 13 }}>No expenses this month</div>}
			{data.map((d, i) => (
				<div key={i} style={{ marginBottom: 10 }}>
					<div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
						<span style={{ color: C.gray700 }}>{d.label}</span>
						<span style={{ fontWeight: 600, color: C.gray800 }}>{fmtFull(d.value)} ({pct(d.value, total)})</span>
					</div>
					<div style={{ height: 6, borderRadius: 3, background: C.gray200 }}>
						<div style={{
							height: 6, borderRadius: 3,
							width: total > 0 ? `${(d.value / total) * 100}%` : "0%",
							background: CHART_COLORS[i % CHART_COLORS.length],
						}} />
					</div>
				</div>
			))}
			{total > 0 && (
				<div style={{ marginTop: 10, paddingTop: 10, borderTop: `1px solid ${C.gray200}`, fontSize: 13, fontWeight: 700, color: C.gray800, textAlign: "right" }}>
					Total: {fmtFull(total)}
				</div>
			)}
		</div>
	);
}

/* ─── Deposit Tracker ─── */
function DepositTracker({ deposits }) {
	const statusColor = { "Overdue": C.danger, "Partially Collected": C.warning, "Pending": C.info };
	const statusBg = { "Overdue": C.dangerLight, "Partially Collected": C.warningLight, "Pending": C.infoLight };

	return (
		<div style={cardStyle}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
				<h3 style={sectionTitle}>Pending Deposits</h3>
				<a href="/app/project-deposit" style={linkBtn}>View All</a>
			</div>
			{deposits.map((d, i) => (
				<a key={i} href={`/app/project-deposit/${d.name}`} style={{
					textDecoration: "none", display: "flex", justifyContent: "space-between", alignItems: "center",
					padding: "8px 0", borderBottom: i < deposits.length - 1 ? `1px solid ${C.gray100}` : "none",
				}}>
					<div>
						<div style={{ fontSize: 13, fontWeight: 600, color: C.gray800 }}>{d.company_authority}</div>
						<div style={{ fontSize: 11, color: C.gray500 }}>
							{d.deposit_type} {"\u00B7"} Due: {d.due_date ? frappe.datetime.str_to_user(d.due_date) : "N/A"}
						</div>
					</div>
					<div style={{ textAlign: "right" }}>
						<div style={{ fontSize: 13, fontWeight: 700, color: C.gray900 }}>{fmtFull(d.amount)}</div>
						<span style={{
							fontSize: 10, fontWeight: 600, padding: "1px 8px", borderRadius: 10,
							background: statusBg[d.status] || C.gray100,
							color: statusColor[d.status] || C.gray500,
						}}>{d.status}{d.days_overdue > 0 ? ` (${d.days_overdue}d)` : ""}</span>
					</div>
				</a>
			))}
		</div>
	);
}

/* ─── Recent Activity ─── */
function RecentActivity({ approved, payrolls }) {
	const items = [
		...approved.map((e) => ({
			label: e.submitted_by_name,
			detail: `${e.approval_status} \u00B7 ${fmtFull(e.amount)}`,
			date: e.posting_date, link: `/app/expense-entry/${e.name}`,
			color: e.approval_status === "Auto Approved" ? C.success : C.info,
		})),
		...payrolls.map((p) => ({
			label: p.project_name,
			detail: `Payroll ${p.payroll_month} ${p.payroll_year} \u00B7 ${fmtFull(p.total_net_pay)}`,
			date: null, link: `/app/payroll-entry/${p.name}`,
			color: C.primary,
		})),
	].slice(0, 8);

	return (
		<div style={cardStyle}>
			<h3 style={{ ...sectionTitle, marginBottom: 14 }}>Recent Transactions</h3>
			{items.length === 0 && <div style={{ color: C.gray400, fontSize: 13 }}>No recent activity</div>}
			{items.map((item, i) => (
				<a key={i} href={item.link} style={{
					textDecoration: "none", display: "flex", alignItems: "center", gap: 10,
					padding: "8px 0", borderBottom: i < items.length - 1 ? `1px solid ${C.gray100}` : "none",
				}}>
					<div style={{ width: 8, height: 8, borderRadius: "50%", background: item.color, flexShrink: 0 }} />
					<div style={{ flex: 1, minWidth: 0 }}>
						<div style={{ fontSize: 13, fontWeight: 600, color: C.gray800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.label}</div>
						<div style={{ fontSize: 11, color: C.gray500 }}>{item.detail}</div>
					</div>
					{item.date && <div style={{ fontSize: 11, color: C.gray400, whiteSpace: "nowrap" }}>{frappe.datetime.prettyDate(item.date)}</div>}
				</a>
			))}
		</div>
	);
}

/* ─── Cashflow Chart (stacked bars) ─── */
function CashflowChart({ chart }) {
	if (!chart || !chart.months || chart.months.length === 0) return null;

	const [hovered, setHovered] = useState(null);
	const categories = ["Payroll", "Expenses", "Advances"];
	const catColors = { "Payroll": C.primary, "Expenses": C.warning, "Advances": C.purple };
	const { months, data: chartData } = chart;

	let maxTotal = 0;
	months.forEach((m) => {
		const md = chartData[m] || {};
		const total = categories.reduce((s, c) => s + (md[c] || 0), 0);
		if (total > maxTotal) maxTotal = total;
	});
	if (maxTotal === 0) maxTotal = 1;

	return (
		<div style={{ ...cardStyle, marginTop: 24 }}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
				<h3 style={sectionTitle}>Monthly Outflow</h3>
				<div style={{ display: "flex", gap: 16 }}>
					{categories.map((c) => (
						<div key={c} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.gray600 }}>
							<div style={{ width: 10, height: 10, borderRadius: 2, background: catColors[c] }} />
							{c}
						</div>
					))}
				</div>
			</div>

			<div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 220, paddingBottom: 28, position: "relative" }}>
				{months.map((m) => {
					const md = chartData[m] || {};
					const total = categories.reduce((s, c) => s + (md[c] || 0), 0);
					const barHeight = (total / maxTotal) * 180;

					return (
						<div key={m} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
							{hovered && hovered.month === m && (
								<div style={{
									position: "absolute", bottom: barHeight + 30, left: "50%", transform: "translateX(-50%)",
									background: C.gray900, color: C.white, padding: "6px 10px", borderRadius: 6,
									fontSize: 11, whiteSpace: "nowrap", zIndex: 10, pointerEvents: "none",
									boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
								}}>
									<div style={{ fontWeight: 600 }}>{hovered.category}</div>
									<div>{fmtFull(hovered.value)}</div>
								</div>
							)}
							<div style={{ fontSize: 11, fontWeight: 600, color: C.gray600, marginBottom: 4 }}>{fmt(total)}</div>
							<div style={{
								width: "100%", maxWidth: 48, height: barHeight, borderRadius: "6px 6px 0 0",
								display: "flex", flexDirection: "column-reverse", overflow: "hidden",
							}}>
								{categories.map((c) => {
									const val = md[c] || 0;
									if (val === 0) return null;
									const segH = (val / total) * barHeight;
									return (
										<div key={c}
											style={{ height: segH, background: catColors[c], cursor: "pointer" }}
											onMouseEnter={() => setHovered({ month: m, category: c, value: val })}
											onMouseLeave={() => setHovered(null)}
										/>
									);
								})}
							</div>
							<div style={{ fontSize: 11, color: C.gray500, marginTop: 6, textAlign: "center" }}>{m}</div>
						</div>
					);
				})}
			</div>
		</div>
	);
}

/* ─── Quick Reports ─── */
function QuickReports() {
	const reports = [
		{ label: "Expense Analysis", route: "/app/query-report/Expense Analysis", icon: "file-text", color: C.primary },
		{ label: "Payroll Summary", route: "/app/query-report/Payroll Summary", icon: "credit-card", color: C.info },
		{ label: "Advance Reconciliation", route: "/app/query-report/Advance Reconciliation", icon: "dollar-sign", color: C.warning },
		{ label: "Budget vs Actual", route: "/app/query-report/Budget vs Actual", icon: "bar-chart-2", color: C.success },
		{ label: "Worker Wise Advance Balance", route: "/app/query-report/Worker Wise Advance Balance", icon: "trending-up", color: C.purple },
		{ label: "Project Cost Summary", route: "/app/query-report/Project Cost Summary", icon: "pie-chart", color: C.danger },
	];

	return (
		<div style={{ marginTop: 24 }}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
				<h3 style={sectionTitle}>Quick Reports</h3>
				<a href="/app/query-report" style={linkBtn}>View All</a>
			</div>
			<div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14 }}>
				{reports.map((r, i) => (
					<a key={i} href={r.route} style={{
						...cardStyle, textDecoration: "none", display: "flex", alignItems: "center", gap: 12,
						transition: "box-shadow 0.15s", cursor: "pointer",
					}}>
						<div style={{
							width: 40, height: 40, borderRadius: 10,
							background: r.color + "15", display: "flex",
							alignItems: "center", justifyContent: "center",
						}}>
							<FeatherIcon name={r.icon} size={18} color={r.color} />
						</div>
						<span style={{ fontSize: 13, fontWeight: 600, color: C.gray700 }}>{r.label}</span>
					</a>
				))}
			</div>
		</div>
	);
}

/* ─── Feather Icon helper ─── */
function FeatherIcon({ name, size = 16, color = C.gray500 }) {
	return (
		<svg width={size} height={size} viewBox="0 0 24 24"
			fill="none" stroke={color} strokeWidth="2"
			strokeLinecap="round" strokeLinejoin="round"
			dangerouslySetInnerHTML={{ __html: getFeatherPath(name) }}
		/>
	);
}

function getFeatherPath(name) {
	const paths = {
		"alert-circle": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
		"flag": '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/>',
		"credit-card": '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
		"file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
		"dollar-sign": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
		"trending-up": '<polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/>',
		"bar-chart-2": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
		"pie-chart": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
	};
	return paths[name] || paths["alert-circle"];
}

/* ─── Shared styles ─── */
const cardStyle = {
	background: C.white, borderRadius: 12, padding: "18px 20px",
	boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
	border: `1px solid ${C.gray200}`,
};

const sectionTitle = { fontSize: 15, fontWeight: 700, color: C.gray800, margin: 0 };

const linkBtn = {
	background: "none", border: "none", color: C.primary,
	fontSize: 13, fontWeight: 600, cursor: "pointer",
	textDecoration: "none", padding: 0,
};

const btnStyle = {
	padding: "8px 20px", borderRadius: 8, border: "none",
	fontWeight: 600, fontSize: 14, cursor: "pointer",
};

const smallBtn = {
	padding: "4px 12px", borderRadius: 6, border: "none",
	fontWeight: 600, fontSize: 12, cursor: "pointer",
	textDecoration: "none", display: "inline-block",
};
