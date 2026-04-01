import * as React from "react";
const { useState, useEffect, useCallback } = React;

/* ─── colour palette ─── */
const C = {
	primary: "#2563eb", primaryLight: "#dbeafe", primaryBg: "#eff6ff",
	success: "#16a34a", successLight: "#dcfce7",
	danger: "#dc2626", dangerLight: "#fee2e2",
	warning: "#f59e0b", warningLight: "#fef3c7",
	info: "#3b82f6", infoLight: "#dbeafe",
	gray50: "#f8fafc", gray100: "#f1f5f9", gray200: "#e2e8f0",
	gray300: "#cbd5e1", gray400: "#94a3b8", gray500: "#64748b",
	gray600: "#475569", gray700: "#334155", gray800: "#1e293b",
	gray900: "#0f172a", white: "#ffffff",
};

const CHART_COLORS = ["#2563eb", "#7c3aed", "#db2777", "#ea580c", "#16a34a", "#0891b2", "#4f46e5", "#059669"];

const fmt = (n) => {
	if (n == null) return "0";
	if (n >= 100000) return `₹${(n / 100000).toFixed(1)}L`;
	if (n >= 1000) return `₹${(n / 1000).toFixed(1)}K`;
	return `₹${Number(n).toLocaleString("en-IN")}`;
};
const fmtFull = (n) => `₹${Number(n || 0).toLocaleString("en-IN")}`;
const pct = (n) => `${Number(n || 0).toFixed(0)}%`;

/* ─── Main App ─── */
export function App({ onRefreshRef }) {
	const [data, setData] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);
	const [alertsCollapsed, setAlertsCollapsed] = useState(false);

	const fetchData = useCallback(async () => {
		setLoading(true);
		setError(null);
		try {
			const r = await frappe.call({ method: "refractec.api.get_admin_dashboard_data" });
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
			{/* Summary Cards */}
			<SummaryCards summary={data.summary} />

			{/* Alerts */}
			{data.alerts.length > 0 && (
				<AlertsPanel alerts={data.alerts} collapsed={alertsCollapsed} onToggle={() => setAlertsCollapsed(!alertsCollapsed)} />
			)}

			{/* Main grid: projects + sidebar */}
			<div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 24, marginTop: 24 }}>
				<div>
					<ProjectCards projects={data.projects} />
				</div>
				<div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
					<WorkerDistribution data={data.worker_by_project} />
					<RecentActivity expenses={data.recent_expenses} advances={data.recent_advances} />
				</div>
			</div>

			{/* Expense Analytics */}
			<ExpenseChart chart={data.expense_chart} />

			{/* Quick Reports */}
			<QuickReports />
		</div>
	);
}

/* ─── Loading / Error ─── */
function Loading() {
	return (
		<div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: 300 }}>
			<div className="frappe-loading" style={{ fontSize: 14, color: C.gray500 }}>Loading dashboard...</div>
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
		{ label: "Active Workers", value: summary.active_workers, icon: "users", color: C.primary, route: "/app/worker?status=Active" },
		{ label: "Active Projects", value: summary.active_projects, icon: "grid", color: C.info, route: "/app/project?status=%5B%22in%22%2C%5B%22Open%22%2C%22In+Progress%22%5D%5D" },
		{ label: "Today's OT Hours", value: `${summary.todays_ot_hours}h`, icon: "clock", color: C.warning, route: "/app/daily-attendance?attendance_date=" + frappe.datetime.get_today() },
		{ label: "Pending Approvals", value: summary.pending_approvals, icon: "alert-circle", color: summary.pending_approvals > 0 ? C.danger : C.success, route: "/app/expense-entry?approval_status=Pending+Approval" },
		{ label: "Payroll This Month", value: fmt(summary.payroll_this_month), icon: "credit-card", color: C.success, route: "/app/payroll-entry" },
		{ label: "Outstanding Advances", value: fmt(summary.outstanding_advances), icon: "dollar-sign", color: summary.outstanding_advances > 0 ? C.warning : C.success, route: "/app/worker-advance?recovery_status=%5B%22in%22%2C%5B%22Unrecovered%22%2C%22Partially+Recovered%22%5D%5D" },
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

/* ─── Alerts Panel ─── */
function AlertsPanel({ alerts, collapsed, onToggle }) {
	const typeStyles = {
		danger: { bg: C.dangerLight, border: C.danger, icon: "alert-triangle" },
		warning: { bg: C.warningLight, border: C.warning, icon: "alert-circle" },
		info: { bg: C.infoLight, border: C.info, icon: "info" },
	};

	return (
		<div style={cardStyle}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: collapsed ? 0 : 16 }}>
				<h3 style={sectionTitle}>Priority Alerts & Notifications</h3>
				<button onClick={onToggle} style={{ ...linkBtn, fontSize: 13 }}>
					{collapsed ? "Expand" : "Collapse"}
				</button>
			</div>
			{!collapsed && (
				<div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
					{alerts.map((a, i) => {
						const s = typeStyles[a.type] || typeStyles.info;
						return (
							<div key={i} style={{
								background: s.bg, borderLeft: `4px solid ${s.border}`,
								borderRadius: 8, padding: "12px 16px",
								display: "flex", justifyContent: "space-between", alignItems: "center",
							}}>
								<div style={{ display: "flex", alignItems: "center", gap: 10 }}>
									<FeatherIcon name={s.icon} size={18} color={s.border} />
									<div>
										<div style={{ fontWeight: 600, fontSize: 13, color: C.gray800 }}>{a.title}</div>
										<div style={{ fontSize: 12, color: C.gray600, marginTop: 2 }}>{a.message}</div>
									</div>
								</div>
								{a.link && (
									<a href={a.link} style={{ ...linkBtn, fontSize: 12, whiteSpace: "nowrap" }}>View</a>
								)}
							</div>
						);
					})}
				</div>
			)}
		</div>
	);
}

/* ─── Project Cards ─── */
function ProjectCards({ projects }) {
	return (
		<div>
			<h3 style={{ ...sectionTitle, marginBottom: 16 }}>Active Project Status</h3>
			<div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
				{projects.map((p) => (
					<ProjectCard key={p.name} project={p} />
				))}
			</div>
		</div>
	);
}

function ProjectCard({ project: p }) {
	const healthColor = p.health === "Over Budget" ? C.danger : p.health === "At Risk" ? C.warning : C.success;
	const healthBg = p.health === "Over Budget" ? C.dangerLight : p.health === "At Risk" ? C.warningLight : C.successLight;
	const utilPct = Math.min(Number(p.budget_utilization_pct || 0), 100);

	return (
		<div style={{ ...cardStyle, cursor: "pointer" }} onClick={() => frappe.set_route("Form", "Project", p.name)}>
			{/* Header */}
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
				<div>
					<div style={{ display: "flex", alignItems: "center", gap: 10 }}>
						<span style={{ fontWeight: 700, fontSize: 15, color: C.gray900 }}>{p.project_name}</span>
						<span style={{
							fontSize: 11, fontWeight: 600, padding: "2px 10px",
							borderRadius: 20, background: healthBg, color: healthColor,
						}}>{p.health}</span>
					</div>
					<div style={{ fontSize: 12, color: C.gray500, marginTop: 4 }}>
						{p.workers} Workers &middot; {p.supervisors} Supervisor{p.supervisors !== 1 ? "s" : ""}
						{p.start_date && ` &middot; Since ${frappe.datetime.str_to_user(p.start_date)}`}
					</div>
				</div>
				<FeatherIcon name="chevron-right" size={18} color={C.gray400} />
			</div>

			{/* Budget bar */}
			<div style={{ marginBottom: 14 }}>
				<div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
					<span style={{ color: C.gray600 }}>Budget: {fmtFull(p.project_budget)}</span>
					<span style={{ fontWeight: 600, color: healthColor }}>{pct(p.budget_utilization_pct)} used</span>
				</div>
				<div style={{ height: 8, borderRadius: 4, background: C.gray200 }}>
					<div style={{
						height: 8, borderRadius: 4, width: `${utilPct}%`,
						background: healthColor, transition: "width 0.5s ease",
					}} />
				</div>
			</div>

			{/* Stats row */}
			<div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
				<StatMini label="Labour" value={fmt(p.total_labor_cost)} />
				<StatMini label="OT Today" value={`${p.todays_ot || 0}h`} />
				<StatMini label="Expenses" value={fmt(p.total_expense_cost)} />
				<StatMini label="This Month" value={fmt(p.expenses_this_month)} />
			</div>
		</div>
	);
}

function StatMini({ label, value }) {
	return (
		<div>
			<div style={{ fontSize: 14, fontWeight: 700, color: C.gray800 }}>{value}</div>
			<div style={{ fontSize: 11, color: C.gray500 }}>{label}</div>
		</div>
	);
}

/* ─── Worker Distribution ─── */
function WorkerDistribution({ data }) {
	const max = Math.max(...data.map((d) => d.count), 1);
	return (
		<div style={cardStyle}>
			<h3 style={{ ...sectionTitle, marginBottom: 14 }}>Worker Assignment by Project</h3>
			{data.length === 0 && <div style={{ color: C.gray400, fontSize: 13 }}>No data</div>}
			{data.map((d, i) => (
				<div key={i} style={{ marginBottom: 12 }}>
					<div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
						<span style={{ color: C.gray700 }}>{d.project_name}</span>
						<span style={{ fontWeight: 600, color: C.gray800 }}>{d.count}</span>
					</div>
					<div style={{ height: 8, borderRadius: 4, background: C.gray200 }}>
						<div style={{
							height: 8, borderRadius: 4, width: `${(d.count / max) * 100}%`,
							background: CHART_COLORS[i % CHART_COLORS.length],
						}} />
					</div>
				</div>
			))}
		</div>
	);
}

/* ─── Recent Activity ─── */
function RecentActivity({ expenses, advances }) {
	const items = [
		...expenses.map((e) => ({
			type: "expense", label: e.submitted_by_name,
			detail: `${e.approval_status} — ${fmtFull(e.amount)}`,
			date: e.posting_date, link: `/app/expense-entry/${e.name}`,
			color: C.warning,
		})),
		...advances.map((a) => ({
			type: "advance", label: a.worker_name,
			detail: `Advance — ${fmtFull(a.amount)}`,
			date: a.advance_date, link: `/app/worker-advance/${a.name}`,
			color: C.info,
		})),
	].sort((a, b) => (b.date || "").localeCompare(a.date || "")).slice(0, 8);

	return (
		<div style={cardStyle}>
			<h3 style={{ ...sectionTitle, marginBottom: 14 }}>Recent Activity</h3>
			{items.length === 0 && <div style={{ color: C.gray400, fontSize: 13 }}>No recent activity</div>}
			{items.map((item, i) => (
				<a key={i} href={item.link} style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < items.length - 1 ? `1px solid ${C.gray100}` : "none" }}>
					<div style={{
						width: 8, height: 8, borderRadius: "50%", background: item.color, flexShrink: 0,
					}} />
					<div style={{ flex: 1, minWidth: 0 }}>
						<div style={{ fontSize: 13, fontWeight: 600, color: C.gray800, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{item.label}</div>
						<div style={{ fontSize: 11, color: C.gray500 }}>{item.detail}</div>
					</div>
					<div style={{ fontSize: 11, color: C.gray400, whiteSpace: "nowrap" }}>
						{item.date ? frappe.datetime.prettyDate(item.date) : ""}
					</div>
				</a>
			))}
		</div>
	);
}

/* ─── Expense Chart (CSS-based stacked bars) ─── */
function BarColumn({ month, types, monthData, colorMap, barHeight }) {
	const [hovered, setHovered] = useState(null);
	const total = types.reduce((s, t) => s + (monthData[t] || 0), 0);

	return (
		<div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", position: "relative" }}>
			{/* Tooltip — rendered outside overflow container */}
			{hovered && (
				<div style={{
					position: "absolute", bottom: barHeight + 30, left: "50%", transform: "translateX(-50%)",
					background: C.gray900, color: C.white, padding: "6px 10px", borderRadius: 6,
					fontSize: 11, whiteSpace: "nowrap", zIndex: 10, pointerEvents: "none",
					boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
				}}>
					<div style={{ fontWeight: 600 }}>{hovered.type}</div>
					<div>{fmtFull(hovered.value)}</div>
					<div style={{
						position: "absolute", top: "100%", left: "50%", transform: "translateX(-50%)",
						width: 0, height: 0, borderLeft: "5px solid transparent",
						borderRight: "5px solid transparent", borderTop: `5px solid ${C.gray900}`,
					}} />
				</div>
			)}
			{/* Value label */}
			<div style={{ fontSize: 11, fontWeight: 600, color: C.gray600, marginBottom: 4 }}>
				{fmt(total)}
			</div>
			{/* Stacked bar */}
			<div style={{
				width: "100%", maxWidth: 48, height: barHeight, borderRadius: "6px 6px 0 0",
				display: "flex", flexDirection: "column-reverse", overflow: "hidden",
			}}>
				{types.map((t) => {
					const val = monthData[t] || 0;
					if (val === 0) return null;
					const segH = (val / total) * barHeight;
					return (
						<div
							key={t}
							style={{ height: segH, background: colorMap[t], cursor: "pointer" }}
							onMouseEnter={() => setHovered({ type: t, value: val })}
							onMouseLeave={() => setHovered(null)}
						/>
					);
				})}
			</div>
			{/* Month label */}
			<div style={{ fontSize: 11, color: C.gray500, marginTop: 6, textAlign: "center" }}>{month}</div>
		</div>
	);
}

function ExpenseChart({ chart }) {
	if (!chart || !chart.months || chart.months.length === 0) {
		return null;
	}

	const { months, types, data: chartData } = chart;
	const colorMap = {};
	types.forEach((t, i) => { colorMap[t] = CHART_COLORS[i % CHART_COLORS.length]; });

	// Find max total for scaling
	let maxTotal = 0;
	months.forEach((m) => {
		const monthData = chartData[m] || {};
		const total = types.reduce((s, t) => s + (monthData[t] || 0), 0);
		if (total > maxTotal) maxTotal = total;
	});
	if (maxTotal === 0) maxTotal = 1;

	return (
		<div style={{ ...cardStyle, marginTop: 24 }}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
				<h3 style={sectionTitle}>Expense Analytics</h3>
				{/* Legend */}
				<div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
					{types.map((t) => (
						<div key={t} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: C.gray600 }}>
							<div style={{ width: 10, height: 10, borderRadius: 2, background: colorMap[t] }} />
							{t}
						</div>
					))}
				</div>
			</div>

			{/* Bars */}
			<div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 220, paddingBottom: 28, position: "relative" }}>
				{months.map((m) => {
					const monthData = chartData[m] || {};
					const total = types.reduce((s, t) => s + (monthData[t] || 0), 0);
					const barHeight = (total / maxTotal) * 180;
					return (
						<BarColumn
							key={m} month={m} types={types}
							monthData={monthData} colorMap={colorMap} barHeight={barHeight}
						/>
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
		{ label: "Budget vs Actual", route: "/app/query-report/Budget vs Actual", icon: "bar-chart-2", color: C.success },
		{ label: "Worker Wise Advance Balance", route: "/app/query-report/Worker Wise Advance Balance", icon: "dollar-sign", color: C.warning },
		{ label: "Payroll Summary", route: "/app/query-report/Payroll Summary", icon: "credit-card", color: C.info },
		{ label: "Attendance Compliance", route: "/app/query-report/Attendance Compliance", icon: "alert-circle", color: C.danger },
		{ label: "Project Cost Summary", route: "/app/query-report/Project Cost Summary", icon: "pie-chart", color: "#7c3aed" },
	];

	return (
		<div style={{ marginTop: 24 }}>
			<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
				<h3 style={sectionTitle}>Quick Reports & Exports</h3>
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

/* ─── Feather Icon helper (uses Frappe's bundled feather icons) ─── */
function FeatherIcon({ name, size = 16, color = C.gray500 }) {
	return (
		<svg
			width={size} height={size} viewBox="0 0 24 24"
			fill="none" stroke={color} strokeWidth="2"
			strokeLinecap="round" strokeLinejoin="round"
			dangerouslySetInnerHTML={{
				__html: getFeatherPath(name),
			}}
		/>
	);
}

function getFeatherPath(name) {
	const paths = {
		"users": '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
		"grid": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>',
		"clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
		"alert-circle": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>',
		"alert-triangle": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>',
		"credit-card": '<rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/>',
		"dollar-sign": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
		"chevron-right": '<polyline points="9 18 15 12 9 6"/>',
		"info": '<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',
		"file-text": '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>',
		"bar-chart-2": '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
		"pie-chart": '<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>',
		"refresh": '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
	};
	return paths[name] || paths["info"];
}

/* ─── Shared styles ─── */
const cardStyle = {
	background: C.white, borderRadius: 12, padding: "18px 20px",
	boxShadow: "0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)",
	border: `1px solid ${C.gray200}`,
};

const sectionTitle = {
	fontSize: 15, fontWeight: 700, color: C.gray800, margin: 0,
};

const linkBtn = {
	background: "none", border: "none", color: C.primary,
	fontSize: 13, fontWeight: 600, cursor: "pointer",
	textDecoration: "none", padding: 0,
};

const btnStyle = {
	padding: "8px 20px", borderRadius: 8, border: "none",
	fontWeight: 600, fontSize: 14, cursor: "pointer",
};
