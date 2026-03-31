import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth, useFrappePostCall } from "frappe-react-sdk";
import Header from "../components/Header";
import Toast from "../components/Toast";
import { useSupervisor } from "../hooks/useSupervisor";

export default function Attendance() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const { context, loading } = useSupervisor();
	const [statuses, setStatuses] = useState({});
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);

	const { call: submitAttendance } = useFrappePostCall(
		"refractec.api.submit_attendance"
	);

	// Redirect if not logged in
	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	// Initialize statuses from context (default all to "Present")
	const initStatuses = useCallback(() => {
		if (context?.workers && Object.keys(statuses).length === 0) {
			const initial = {};
			context.workers.forEach((w) => {
				// If attendance already exists for today, use that status
				const existing = context.today_attendance?.[w.worker];
				initial[w.worker] = existing?.status || "Present";
			});
			setStatuses(initial);
		}
	}, [context, statuses]);

	if (!loading && context) {
		initStatuses();
	}

	if (loading || authLoading) {
		return (
			<>
				<Header title="Attendance" showBack />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
				</div>
			</>
		);
	}

	// Already submitted
	if (context?.attendance_submitted) {
		const records = context.today_attendance || {};
		const presentCount = Object.values(records).filter(
			(r) => r.status === "Present"
		).length;
		const absentCount = Object.values(records).filter(
			(r) => r.status === "Absent"
		).length;

		return (
			<>
				<Header
					title="Attendance"
					subtitle={context?.today}
					showBack
				/>
				<div className="app-content">
					<div className="submitted-overlay">
						<div className="check-icon">✅</div>
						<h2>Attendance Submitted</h2>
						<p>Today's attendance has been finalized.</p>
						<div style={{ marginTop: 20 }}>
							<div className="summary-row">
								<span>Present</span>
								<span className="count" style={{ color: "var(--success)" }}>
									{presentCount}
								</span>
							</div>
							<div className="summary-row">
								<span>Absent</span>
								<span className="count" style={{ color: "var(--danger)" }}>
									{absentCount}
								</span>
							</div>
						</div>
					</div>
				</div>
			</>
		);
	}

	// Past cutoff
	if (context?.is_past_cutoff) {
		return (
			<>
				<Header title="Attendance" subtitle={context?.today} showBack />
				<div className="app-content">
					<div className="submitted-overlay">
						<div className="check-icon">⏰</div>
						<h2>Cutoff Time Passed</h2>
						<p>
							Attendance must be submitted before {context.cutoff_hour}:00.
							Please contact admin.
						</p>
					</div>
				</div>
			</>
		);
	}

	const toggleStatus = (workerId, status) => {
		setStatuses((prev) => ({ ...prev, [workerId]: status }));
	};

	const presentCount = Object.values(statuses).filter(
		(s) => s === "Present"
	).length;
	const absentCount = Object.values(statuses).filter(
		(s) => s === "Absent"
	).length;

	const handleSubmit = async () => {
		setSubmitting(true);
		try {
			const data = context.workers.map((w) => ({
				worker: w.worker,
				status: statuses[w.worker] || "Present",
			}));
			await submitAttendance({
				project: context.project.name,
				attendance_data: JSON.stringify(data),
			});
			setToast({ message: "Attendance submitted!", type: "success" });
			setTimeout(() => navigate("/"), 1500);
		} catch (err) {
			setToast({
				message: err?.message || "Failed to submit",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<>
			<Header
				title="Attendance"
				subtitle={`${context?.project?.project_name} — ${context?.today}`}
				showBack
			/>
			{toast && (
				<Toast
					message={toast.message}
					type={toast.type}
					onClose={() => setToast(null)}
				/>
			)}
			<div className="app-content">
				<div className="summary-row" style={{ marginBottom: 12 }}>
					<span>
						<strong style={{ color: "var(--success)" }}>{presentCount}</strong>{" "}
						Present
					</span>
					<span>
						<strong style={{ color: "var(--danger)" }}>{absentCount}</strong>{" "}
						Absent
					</span>
					<span>
						<strong>{context?.workers?.length || 0}</strong> Total
					</span>
				</div>

				<div className="worker-list">
					{context?.workers?.map((w) => (
						<div className="worker-row" key={w.worker}>
							<div className="worker-info">
								<div className="worker-name">{w.worker_name}</div>
								<div className="worker-type">{w.worker_type}</div>
							</div>
							<div className="toggle-group">
								<button
									className={`toggle-btn present ${
										statuses[w.worker] === "Present" ? "active" : ""
									}`}
									onClick={() => toggleStatus(w.worker, "Present")}
								>
									P
								</button>
								<button
									className={`toggle-btn absent ${
										statuses[w.worker] === "Absent" ? "active" : ""
									}`}
									onClick={() => toggleStatus(w.worker, "Absent")}
								>
									A
								</button>
							</div>
						</div>
					))}
				</div>
			</div>

			<div className="submit-bar">
				<button
					className="btn btn-success"
					onClick={handleSubmit}
					disabled={submitting}
				>
					{submitting ? (
						<span className="spinner" />
					) : (
						`Submit Attendance (${presentCount}P / ${absentCount}A)`
					)}
				</button>
			</div>
		</>
	);
}
