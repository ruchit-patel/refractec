import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth, useFrappePostCall } from "frappe-react-sdk";
import Header from "../components/Header";
import Toast from "../components/Toast";
import { useSupervisor } from "../hooks/useSupervisor";

export default function Advance() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const { context, loading } = useSupervisor();
	const [worker, setWorker] = useState("");
	const [amount, setAmount] = useState("");
	const [paymentMode, setPaymentMode] = useState("Cash");
	const [referenceNo, setReferenceNo] = useState("");
	const [purpose, setPurpose] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);

	// History state
	const [history, setHistory] = useState(null);
	const [historyLoading, setHistoryLoading] = useState(false);

	const { call: submitAdvance } = useFrappePostCall(
		"refractec.api.submit_advance"
	);
	const { call: fetchHistory } = useFrappePostCall(
		"refractec.api.get_advance_history"
	);

	const loadHistory = useCallback(
		async (workerVal) => {
			if (!context?.project?.name) return;
			setHistoryLoading(true);
			try {
				const res = await fetchHistory({
					project: context.project.name,
					worker: workerVal || "",
				});
				setHistory(res?.message || null);
			} catch {
				setHistory(null);
			} finally {
				setHistoryLoading(false);
			}
		},
		[context?.project?.name, fetchHistory]
	);

	// Load history when worker changes or on mount
	useEffect(() => {
		if (context?.project?.name) {
			loadHistory(worker);
		}
	}, [worker, context?.project?.name, loadHistory]);

	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	if (loading || authLoading) {
		return (
			<>
				<Header title="Worker Advance" showBack />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
				</div>
			</>
		);
	}

	const handleSubmit = async (e) => {
		e.preventDefault();

		if (!worker) {
			setToast({ message: "Please select a worker", type: "error" });
			return;
		}
		if (!amount || parseFloat(amount) <= 0) {
			setToast({ message: "Please enter a valid amount", type: "error" });
			return;
		}
		if (paymentMode !== "Cash" && !referenceNo.trim()) {
			setToast({ message: "Reference No is required for non-cash payments", type: "error" });
			return;
		}

		setSubmitting(true);
		try {
			const res = await submitAdvance({
				project: context.project.name,
				worker,
				amount: parseFloat(amount),
				payment_mode: paymentMode,
				reference_no: referenceNo || "",
				purpose: purpose || "",
			});

			setToast({
				message: res?.message?.message || "Advance submitted!",
				type: "success",
			});

			// Reset form
			setAmount("");
			setPaymentMode("Cash");
			setReferenceNo("");
			setPurpose("");

			// Refresh history to show new advance
			loadHistory(worker);

			setTimeout(() => navigate("/"), 1500);
		} catch (err) {
			setToast({
				message: err?.message || "Failed to submit advance",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	const recoveryColor = (status) => {
		if (status === "Fully Recovered") return "var(--success)";
		if (status === "Partially Recovered") return "var(--warning)";
		return "var(--danger)";
	};

	const formatDate = (d) => {
		if (!d) return "";
		const dt = new Date(d);
		return dt.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
	};

	return (
		<>
			<Header
				title="Worker Advance"
				subtitle={context?.project?.project_name}
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
				<form className="expense-form" onSubmit={handleSubmit}>
					{/* Worker */}
					<div className="form-group">
						<label>Worker</label>
						<select
							className="form-select"
							value={worker}
							onChange={(e) => setWorker(e.target.value)}
						>
							<option value="">Select worker...</option>
							{(context?.workers || []).map((w) => (
								<option key={w.worker} value={w.worker}>
									{w.worker_name} ({w.worker_type})
								</option>
							))}
						</select>
					</div>

					{/* Amount */}
					<div className="form-group">
						<label>Amount (₹)</label>
						<input
							className="form-input"
							type="number"
							inputMode="decimal"
							placeholder="0.00"
							value={amount}
							onChange={(e) => setAmount(e.target.value)}
							min="0"
							step="0.01"
						/>
					</div>

					{/* Payment Mode */}
					<div className="form-group">
						<label>Payment Mode</label>
						<select
							className="form-select"
							value={paymentMode}
							onChange={(e) => setPaymentMode(e.target.value)}
						>
							<option value="Cash">Cash</option>
							<option value="Bank Transfer">Bank Transfer</option>
							<option value="UPI">UPI</option>
						</select>
					</div>

					{/* Reference No (non-cash only) */}
					{paymentMode !== "Cash" && (
						<div className="form-group">
							<label>Reference No</label>
							<input
								className="form-input"
								type="text"
								placeholder={paymentMode === "UPI" ? "UPI Transaction ID" : "Bank Reference No"}
								value={referenceNo}
								onChange={(e) => setReferenceNo(e.target.value)}
							/>
						</div>
					)}

					{/* Purpose */}
					<div className="form-group">
						<label>Purpose (optional)</label>
						<textarea
							className="form-textarea"
							placeholder="Why is this advance being given?"
							value={purpose}
							onChange={(e) => setPurpose(e.target.value)}
							rows={3}
						/>
					</div>

					{/* Submit */}
					<button
						className="btn btn-primary"
						type="submit"
						disabled={submitting}
					>
						{submitting ? <span className="spinner" /> : "Submit Advance"}
					</button>
				</form>

				{/* Advance History */}
				<div className="section-divider" style={{ marginTop: 28 }}>
					{worker ? "Advance History" : "All Advances — This Project"}
				</div>

				{historyLoading && (
					<div style={{ textAlign: "center", padding: 20 }}>
						<div className="spinner dark" style={{ width: 24, height: 24 }} />
					</div>
				)}

				{!historyLoading && history && (
					<>
						{/* Summary cards */}
						<div style={{
							display: "flex", gap: 8, marginBottom: 12,
						}}>
							<div style={{
								flex: 1, background: "white", borderRadius: "var(--radius-sm)",
								padding: "10px 12px", boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
							}}>
								<div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 2 }}>Advanced</div>
								<div style={{ fontSize: 16, fontWeight: 700, color: "var(--gray-900)" }}>
									₹{history.total_advanced.toLocaleString("en-IN")}
								</div>
							</div>
							<div style={{
								flex: 1, background: "white", borderRadius: "var(--radius-sm)",
								padding: "10px 12px", boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
							}}>
								<div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 2 }}>Recovered</div>
								<div style={{ fontSize: 16, fontWeight: 700, color: "var(--success)" }}>
									₹{history.total_recovered.toLocaleString("en-IN")}
								</div>
							</div>
							<div style={{
								flex: 1, background: "white", borderRadius: "var(--radius-sm)",
								padding: "10px 12px", boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
							}}>
								<div style={{ fontSize: 11, color: "var(--gray-500)", marginBottom: 2 }}>Outstanding</div>
								<div style={{ fontSize: 16, fontWeight: 700, color: history.total_outstanding > 0 ? "var(--danger)" : "var(--success)" }}>
									₹{history.total_outstanding.toLocaleString("en-IN")}
								</div>
							</div>
						</div>

						{/* Advance list */}
						{history.advances.length === 0 ? (
							<div style={{ textAlign: "center", padding: "24px 0", color: "var(--gray-400)" }}>
								No advances found
							</div>
						) : (
							<div className="worker-list">
								{history.advances.map((adv) => (
									<div className="worker-row" key={adv.name} style={{ flexDirection: "column", alignItems: "stretch", gap: 6 }}>
										<div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
											<div>
												{!worker && (
													<div className="worker-name">{adv.worker_name}</div>
												)}
												<div style={{ fontSize: 12, color: "var(--gray-500)" }}>
													{formatDate(adv.advance_date)} &middot; {adv.payment_mode}
												</div>
											</div>
											<div style={{ textAlign: "right" }}>
												<div style={{ fontSize: 16, fontWeight: 700 }}>
													₹{adv.amount.toLocaleString("en-IN")}
												</div>
												<div style={{
													fontSize: 11, fontWeight: 600,
													color: recoveryColor(adv.recovery_status),
												}}>
													{adv.recovery_status}
												</div>
											</div>
										</div>
										{adv.purpose && (
											<div style={{ fontSize: 12, color: "var(--gray-600)", fontStyle: "italic" }}>
												{adv.purpose}
											</div>
										)}
									</div>
								))}
							</div>
						)}
					</>
				)}
			</div>
		</>
	);
}
