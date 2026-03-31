import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth, useFrappePostCall } from "frappe-react-sdk";
import Header from "../components/Header";
import Toast from "../components/Toast";
import { useSupervisor } from "../hooks/useSupervisor";

export default function Overtime() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const { context, loading } = useSupervisor();
	const [otHours, setOtHours] = useState({});
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);

	const { call: submitOvertime } = useFrappePostCall(
		"refractec.api.submit_overtime"
	);

	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	if (loading || authLoading) {
		return (
			<>
				<Header title="Overtime" showBack />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
				</div>
			</>
		);
	}

	if (!context?.attendance_submitted) {
		return (
			<>
				<Header title="Overtime" showBack />
				<div className="app-content">
					<div className="submitted-overlay">
						<div className="check-icon">📋</div>
						<h2>Attendance Not Submitted</h2>
						<p>Please submit today's attendance first before recording overtime.</p>
						<button
							className="btn btn-primary"
							style={{ marginTop: 20, maxWidth: 240 }}
							onClick={() => navigate("/attendance")}
						>
							Go to Attendance
						</button>
					</div>
				</div>
			</>
		);
	}

	// Filter to only present workers
	const presentWorkers = context.workers.filter((w) => {
		const record = context.today_attendance?.[w.worker];
		return record && record.status === "Present";
	});

	// Check if OT already recorded
	const existingOt = context.today_attendance || {};
	const hasExistingOt = Object.values(existingOt).some(
		(r) => r.overtime_hours > 0
	);

	const maxHours = context.max_ot_hours || 6;
	const hourButtons = Array.from({ length: maxHours }, (_, i) => i + 1);

	const toggleOt = (workerId, hours) => {
		setOtHours((prev) => ({
			...prev,
			[workerId]: prev[workerId] === hours ? 0 : hours,
		}));
	};

	const totalOtWorkers = Object.values(otHours).filter((h) => h > 0).length;
	const totalOtHours = Object.values(otHours).reduce((sum, h) => sum + h, 0);

	const handleSubmit = async () => {
		const data = presentWorkers
			.map((w) => ({
				worker: w.worker,
				overtime_hours: otHours[w.worker] || 0,
			}))
			.filter((d) => d.overtime_hours > 0);

		if (data.length === 0) {
			setToast({ message: "No overtime hours marked", type: "error" });
			return;
		}

		setSubmitting(true);
		try {
			await submitOvertime({
				project: context.project.name,
				overtime_data: JSON.stringify(data),
			});
			setToast({ message: "Overtime submitted!", type: "success" });
			setTimeout(() => navigate("/"), 1500);
		} catch (err) {
			setToast({
				message: err?.message || "Failed to submit overtime",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	if (hasExistingOt) {
		return (
			<>
				<Header
					title="Overtime"
					subtitle={context?.today}
					showBack
				/>
				<div className="app-content">
					<div className="submitted-overlay">
						<div className="check-icon">✅</div>
						<h2>Overtime Recorded</h2>
						<p>Today's overtime has already been submitted.</p>
					</div>
					<div className="worker-list" style={{ marginTop: 16 }}>
						{presentWorkers.map((w) => {
							const ot = existingOt[w.worker]?.overtime_hours || 0;
							if (ot === 0) return null;
							return (
								<div className="worker-row" key={w.worker}>
									<div className="worker-info">
										<div className="worker-name">{w.worker_name}</div>
									</div>
									<div
										style={{
											fontWeight: 700,
											color: "var(--warning)",
											fontSize: 16,
										}}
									>
										{ot}h
									</div>
								</div>
							);
						})}
					</div>
				</div>
			</>
		);
	}

	return (
		<>
			<Header
				title="Overtime"
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
				{presentWorkers.length === 0 ? (
					<div className="submitted-overlay">
						<div className="check-icon">🚫</div>
						<h2>No Present Workers</h2>
						<p>No workers marked present today.</p>
					</div>
				) : (
					<>
						<p className="section-divider">
							Present Workers ({presentWorkers.length}) — Tap hours
						</p>

						<div className="worker-list">
							{presentWorkers.map((w) => (
								<div className="worker-row" key={w.worker}>
									<div className="worker-info">
										<div className="worker-name">{w.worker_name}</div>
										<div className="worker-type">
											{otHours[w.worker]
												? `${otHours[w.worker]}h OT`
												: "No OT"}
										</div>
									</div>
									<div className="ot-buttons">
										{hourButtons.map((h) => (
											<button
												key={h}
												className={`ot-btn ${
													otHours[w.worker] === h ? "active" : ""
												}`}
												onClick={() => toggleOt(w.worker, h)}
											>
												{h}
											</button>
										))}
									</div>
								</div>
							))}
						</div>
					</>
				)}
			</div>

			{presentWorkers.length > 0 && (
				<div className="submit-bar">
					<button
						className="btn btn-success"
						onClick={handleSubmit}
						disabled={submitting || totalOtWorkers === 0}
					>
						{submitting ? (
							<span className="spinner" />
						) : (
							`Submit OT (${totalOtWorkers} workers, ${totalOtHours}h total)`
						)}
					</button>
				</div>
			)}
		</>
	);
}
