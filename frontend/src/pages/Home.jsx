import { useNavigate } from "react-router-dom";
import { useFrappeAuth } from "frappe-react-sdk";
import Header from "../components/Header";
import { useSupervisor } from "../hooks/useSupervisor";

export default function Home() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading, logout } = useFrappeAuth();
	const { context, loading, error } = useSupervisor();

	// Redirect to login if not authenticated
	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	if (authLoading || loading) {
		return (
			<>
				<Header title="Refractec" />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
					<p style={{ marginTop: 16, color: "var(--gray-500)" }}>Loading...</p>
				</div>
			</>
		);
	}

	if (error) {
		return (
			<>
				<Header title="Refractec" />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<p style={{ color: "var(--danger)", marginBottom: 16 }}>{error}</p>
					<button className="btn btn-primary" onClick={() => { logout(); navigate("/login"); }}>
						Logout
					</button>
				</div>
			</>
		);
	}

	const attendanceDone = context?.attendance_submitted;
	const hasOtData = context?.today_attendance &&
		Object.values(context.today_attendance).some((r) => r.overtime_hours > 0);

	return (
		<>
			<Header
				title={context?.project?.project_name || "Refractec"}
				subtitle={`Hi, ${context?.supervisor?.worker_name}`}
			/>
			<div className="app-content">
				<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
					<p style={{ fontSize: 13, color: "var(--gray-500)" }}>
						{context?.today}
					</p>
					<button
						onClick={() => { logout(); navigate("/login"); }}
						style={{
							background: "none", border: "none", color: "var(--danger)",
							fontSize: 13, fontWeight: 600, cursor: "pointer"
						}}
					>
						Logout
					</button>
				</div>

				{/* Fund Balance */}
				{context?.fund && context.fund.total_given > 0 && (
					<div style={{
						background: "white", borderRadius: "var(--radius)",
						padding: "14px 16px", marginBottom: 16,
						boxShadow: "0 1px 3px rgba(0,0,0,0.08)",
					}}>
						<div style={{ fontSize: 13, fontWeight: 600, color: "var(--gray-500)", marginBottom: 8 }}>
							Fund Balance
						</div>
						<div style={{ display: "flex", gap: 12 }}>
							<div style={{ flex: 1 }}>
								<div style={{ fontSize: 11, color: "var(--gray-400)" }}>Cash</div>
								<div style={{ fontSize: 18, fontWeight: 700, color: context.fund.cash_balance >= 0 ? "var(--gray-900)" : "var(--danger)" }}>
									₹{context.fund.cash_balance.toLocaleString("en-IN")}
								</div>
							</div>
							<div style={{ flex: 1 }}>
								<div style={{ fontSize: 11, color: "var(--gray-400)" }}>Bank</div>
								<div style={{ fontSize: 18, fontWeight: 700, color: context.fund.bank_balance >= 0 ? "var(--gray-900)" : "var(--danger)" }}>
									₹{context.fund.bank_balance.toLocaleString("en-IN")}
								</div>
							</div>
							<div style={{ flex: 1 }}>
								<div style={{ fontSize: 11, color: "var(--gray-400)" }}>Total</div>
								<div style={{ fontSize: 18, fontWeight: 700, color: context.fund.balance >= 0 ? "var(--success)" : "var(--danger)" }}>
									₹{context.fund.balance.toLocaleString("en-IN")}
								</div>
							</div>
						</div>
					</div>
				)}

				<div className="home-grid">
					{/* 1. Attendance */}
					<button className="home-card" onClick={() => navigate("/attendance")}>
						<div className="icon blue">📋</div>
						<div className="card-info">
							<div>Attendance</div>
							<div className="card-desc">Mark present / absent for today</div>
							{attendanceDone && (
								<span className="status-badge done">Submitted</span>
							)}
							{!attendanceDone && context?.is_past_cutoff && (
								<span className="status-badge" style={{ background: "#fee2e2", color: "var(--danger)" }}>
									Cutoff Passed
								</span>
							)}
						</div>
						<span className="arrow">&#8250;</span>
					</button>

					{/* 2. Overtime */}
					<button
						className="home-card"
						onClick={() => navigate("/overtime")}
						disabled={!attendanceDone}
						style={!attendanceDone ? { opacity: 0.5 } : {}}
					>
						<div className="icon orange">⏱️</div>
						<div className="card-info">
							<div>Overtime</div>
							<div className="card-desc">
								{attendanceDone
									? `Up to ${context?.max_ot_hours || 6} hours per worker`
									: "Submit attendance first"}
							</div>
							{hasOtData && (
								<span className="status-badge done">Recorded</span>
							)}
						</div>
						<span className="arrow">&#8250;</span>
					</button>

					{/* 3. Expense Entry */}
					<button className="home-card" onClick={() => navigate("/expense")}>
						<div className="icon green">💰</div>
						<div className="card-info">
							<div>Expense Entry</div>
							<div className="card-desc">Submit expense with bill</div>
						</div>
						<span className="arrow">&#8250;</span>
					</button>

					{/* 4. Worker Advance */}
					<button className="home-card" onClick={() => navigate("/advance")}>
						<div className="icon" style={{ background: "#e0e7ff" }}>💵</div>
						<div className="card-info">
							<div>Worker Advance</div>
							<div className="card-desc">Give advance to a worker</div>
						</div>
						<span className="arrow">&#8250;</span>
					</button>

					{/* 5. My Expenses */}
					<button className="home-card" onClick={() => navigate("/my-expenses")}>
						<div className="icon" style={{ background: "#fef3c7" }}>📒</div>
						<div className="card-info">
							<div>My Expenses</div>
							<div className="card-desc">View & edit submitted expenses</div>
						</div>
						<span className="arrow">&#8250;</span>
					</button>
				</div>
			</div>
		</>
	);
}
