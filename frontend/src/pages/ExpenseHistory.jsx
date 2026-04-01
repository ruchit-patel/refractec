import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth, useFrappePostCall } from "frappe-react-sdk";
import Header from "../components/Header";
import Toast from "../components/Toast";
import { useSupervisor } from "../hooks/useSupervisor";

export default function ExpenseHistory() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const { context, loading } = useSupervisor();
	const [expenses, setExpenses] = useState([]);
	const [listLoading, setListLoading] = useState(true);
	const [editing, setEditing] = useState(null); // expense name being edited
	const [editForm, setEditForm] = useState({});
	const [expenseTypes, setExpenseTypes] = useState([]);
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);

	const { call: fetchExpenses } = useFrappePostCall("refractec.api.get_my_expenses");
	const { call: editExpense } = useFrappePostCall("refractec.api.edit_expense");
	const { call: fetchExpenseTypes } = useFrappePostCall("refractec.api.get_expense_types");

	const loadExpenses = async () => {
		if (!context?.project?.name) return;
		setListLoading(true);
		try {
			const res = await fetchExpenses({ project: context.project.name });
			setExpenses(res?.message || []);
		} catch {
			setExpenses([]);
		} finally {
			setListLoading(false);
		}
	};

	useEffect(() => {
		if (context?.project?.name) loadExpenses();
	}, [context?.project?.name]);

	useEffect(() => {
		fetchExpenseTypes({}).then((res) => {
			if (res?.message) setExpenseTypes(res.message);
		}).catch(() => {});
	}, [fetchExpenseTypes]);

	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	if (loading || authLoading) {
		return (
			<>
				<Header title="My Expenses" showBack />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
				</div>
			</>
		);
	}

	const startEdit = (exp) => {
		setEditing(exp.name);
		setEditForm({
			expense_type: exp.expense_type,
			amount: exp.amount,
			description: exp.description || "",
			expense_date: exp.expense_date,
		});
	};

	const cancelEdit = () => {
		setEditing(null);
		setEditForm({});
	};

	const handleSave = async (expName) => {
		setSubmitting(true);
		try {
			const res = await editExpense({
				expense_name: expName,
				expense_type: editForm.expense_type,
				amount: parseFloat(editForm.amount),
				description: editForm.description,
				expense_date: editForm.expense_date,
			});
			setToast({
				message: res?.message?.message || "Expense updated!",
				type: "success",
			});
			setEditing(null);
			setEditForm({});
			loadExpenses();
		} catch (err) {
			setToast({
				message: err?.message || "Failed to update expense",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	const statusColor = (status) => {
		if (status === "Auto Approved" || status === "Manually Approved") return "var(--success)";
		if (status === "Rejected") return "var(--danger)";
		return "var(--warning)";
	};

	const formatDate = (d) => {
		if (!d) return "";
		return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
	};

	return (
		<>
			<Header
				title="My Expenses"
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
				{listLoading && (
					<div style={{ textAlign: "center", padding: 30 }}>
						<div className="spinner dark" style={{ width: 24, height: 24 }} />
					</div>
				)}

				{!listLoading && expenses.length === 0 && (
					<div style={{ textAlign: "center", padding: "40px 0", color: "var(--gray-400)" }}>
						<div style={{ fontSize: 40, marginBottom: 8 }}>📄</div>
						No expenses found
					</div>
				)}

				{!listLoading && expenses.length > 0 && (
					<div className="worker-list">
						{expenses.map((exp) => {
							const isEditing = editing === exp.name;
							const isCancelled = exp.docstatus === 2;

							return (
								<div className="worker-row" key={exp.name} style={{
									flexDirection: "column", alignItems: "stretch", gap: 10,
									opacity: isCancelled ? 0.5 : 1,
								}}>
									{/* View mode */}
									{!isEditing && (
										<>
											<div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
												<div>
													<div className="worker-name">{exp.expense_type_name}</div>
													<div style={{ fontSize: 12, color: "var(--gray-500)", marginTop: 2 }}>
														{formatDate(exp.expense_date)}
													</div>
													{exp.description && (
														<div style={{ fontSize: 12, color: "var(--gray-600)", marginTop: 4, fontStyle: "italic" }}>
															{exp.description}
														</div>
													)}
												</div>
												<div style={{ textAlign: "right" }}>
													<div style={{ fontSize: 16, fontWeight: 700 }}>
														₹{Number(exp.amount).toLocaleString("en-IN")}
													</div>
													<div style={{
														fontSize: 11, fontWeight: 600,
														color: statusColor(exp.approval_status),
													}}>
														{isCancelled ? "Cancelled" : exp.approval_status}
													</div>
												</div>
											</div>

											{/* Flagged badge */}
											{exp.is_flagged === 1 && (
												<div style={{
													fontSize: 11, color: "var(--warning)", fontWeight: 600,
													display: "flex", alignItems: "center", gap: 4,
												}}>
													⚑ Flagged{exp.flag_reason ? `: ${exp.flag_reason}` : ""}
												</div>
											)}

											{/* Edit button — only for submitted, non-cancelled */}
											{!isCancelled && exp.docstatus === 1 && (
												<button
													onClick={() => startEdit(exp)}
													style={{
														background: "var(--gray-100)", border: "none",
														borderRadius: 8, padding: "8px 0",
														fontSize: 13, fontWeight: 600,
														color: "var(--primary)", cursor: "pointer",
													}}
												>
													Edit Expense
												</button>
											)}
										</>
									)}

									{/* Edit mode */}
									{isEditing && (
										<>
											<div className="form-group" style={{ marginBottom: 10 }}>
												<label style={{ fontSize: 12, fontWeight: 600 }}>Expense Type</label>
												<select
													className="form-select"
													value={editForm.expense_type}
													onChange={(e) => setEditForm({ ...editForm, expense_type: e.target.value })}
												>
													{expenseTypes.map((t) => (
														<option key={t.name} value={t.name}>{t.expense_type_name}</option>
													))}
												</select>
											</div>

											<div className="form-group" style={{ marginBottom: 10 }}>
												<label style={{ fontSize: 12, fontWeight: 600 }}>Expense Date</label>
												<input
													className="form-input"
													type="date"
													value={editForm.expense_date}
													onChange={(e) => setEditForm({ ...editForm, expense_date: e.target.value })}
													max={new Date().toISOString().split("T")[0]}
												/>
											</div>

											<div className="form-group" style={{ marginBottom: 10 }}>
												<label style={{ fontSize: 12, fontWeight: 600 }}>Amount (₹)</label>
												<input
													className="form-input"
													type="number"
													inputMode="decimal"
													value={editForm.amount}
													onChange={(e) => setEditForm({ ...editForm, amount: e.target.value })}
													min="0"
													step="0.01"
												/>
											</div>

											<div className="form-group" style={{ marginBottom: 10 }}>
												<label style={{ fontSize: 12, fontWeight: 600 }}>Description</label>
												<textarea
													className="form-textarea"
													value={editForm.description}
													onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
													rows={2}
												/>
											</div>

											<div style={{ display: "flex", gap: 8 }}>
												<button
													onClick={() => handleSave(exp.name)}
													disabled={submitting}
													style={{
														flex: 1, background: "var(--primary)", color: "white",
														border: "none", borderRadius: 8, padding: "10px 0",
														fontSize: 13, fontWeight: 600, cursor: "pointer",
													}}
												>
													{submitting ? "Saving..." : "Save & Flag"}
												</button>
												<button
													onClick={cancelEdit}
													disabled={submitting}
													style={{
														flex: 1, background: "var(--gray-200)", color: "var(--gray-700)",
														border: "none", borderRadius: 8, padding: "10px 0",
														fontSize: 13, fontWeight: 600, cursor: "pointer",
													}}
												>
													Cancel
												</button>
											</div>

											<div style={{ fontSize: 11, color: "var(--warning)", textAlign: "center", marginTop: 4 }}>
												Editing will flag this expense for admin review
											</div>
										</>
									)}
								</div>
							);
						})}
					</div>
				)}
			</div>
		</>
	);
}
