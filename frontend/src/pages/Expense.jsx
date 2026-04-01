import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth, useFrappePostCall, useFrappeFileUpload } from "frappe-react-sdk";
import Header from "../components/Header";
import Toast from "../components/Toast";
import { useSupervisor } from "../hooks/useSupervisor";

export default function Expense() {
	const navigate = useNavigate();
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const { context, loading } = useSupervisor();
	const [expenseTypes, setExpenseTypes] = useState([]);
	const [expenseType, setExpenseType] = useState("");
	const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split("T")[0]);
	const [amount, setAmount] = useState("");
	const [description, setDescription] = useState("");
	const [file, setFile] = useState(null);
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);
	const fileInputRef = useRef(null);

	const { call: fetchExpenseTypes } = useFrappePostCall(
		"refractec.api.get_expense_types"
	);
	const { call: createExpense } = useFrappePostCall(
		"refractec.api.create_expense"
	);
	const { call: finalizeExpense } = useFrappePostCall(
		"refractec.api.finalize_expense"
	);
	const { upload } = useFrappeFileUpload();

	useEffect(() => {
		fetchExpenseTypes({}).then((res) => {
			if (res?.message) {
				setExpenseTypes(res.message);
			}
		}).catch(() => {});
	}, [fetchExpenseTypes]);

	if (!authLoading && (!currentUser || currentUser === "Guest")) {
		navigate("/login", { replace: true });
		return null;
	}

	if (loading || authLoading) {
		return (
			<>
				<Header title="Expense Entry" showBack />
				<div className="app-content" style={{ textAlign: "center", paddingTop: 60 }}>
					<div className="spinner dark" style={{ width: 32, height: 32 }} />
				</div>
			</>
		);
	}

	const handleFileChange = (e) => {
		const selected = e.target.files?.[0];
		if (selected) {
			setFile(selected);
		}
	};

	const handleSubmit = async (e) => {
		e.preventDefault();

		if (!expenseType) {
			setToast({ message: "Please select expense type", type: "error" });
			return;
		}
		if (!amount || parseFloat(amount) <= 0) {
			setToast({ message: "Please enter a valid amount", type: "error" });
			return;
		}

		setSubmitting(true);
		try {
			// Step 1: Create draft expense
			const res = await createExpense({
				project: context.project.name,
				expense_type: expenseType,
				amount: parseFloat(amount),
				description: description || "",
				expense_date: expenseDate,
			});

			const expenseName = res?.message?.name;
			if (!expenseName) {
				throw new Error("Failed to create expense");
			}

			// Step 2: Upload file attachment if provided
			if (file) {
				await upload(file, {
					doctype: "Expense Entry",
					docname: expenseName,
					fieldname: "bill_attachment",
					isPrivate: true,
				});
			}

			// Step 3: Submit the expense (picks up attached file)
			const finalRes = await finalizeExpense({
				expense_name: expenseName,
			});

			const status = finalRes?.message?.approval_status || "Submitted";
			setToast({
				message: `Expense submitted! Status: ${status}`,
				type: "success",
			});

			// Reset form
			setExpenseType("");
			setExpenseDate(new Date().toISOString().split("T")[0]);
			setAmount("");
			setDescription("");
			setFile(null);

			setTimeout(() => navigate("/"), 1500);
		} catch (err) {
			setToast({
				message: err?.message || "Failed to submit expense",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<>
			<Header
				title="Expense Entry"
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
					{/* Expense Type */}
					<div className="form-group">
						<label>Expense Type</label>
						<select
							className="form-select"
							value={expenseType}
							onChange={(e) => setExpenseType(e.target.value)}
						>
							<option value="">Select type...</option>
							{expenseTypes.map((t) => (
								<option key={t.name} value={t.name}>
									{t.expense_type_name}
								</option>
							))}
						</select>
					</div>

					{/* Expense Date */}
					<div className="form-group">
						<label>Expense Date</label>
						<input
							className="form-input"
							type="date"
							value={expenseDate}
							onChange={(e) => setExpenseDate(e.target.value)}
							max={new Date().toISOString().split("T")[0]}
						/>
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

					{/* Description */}
					<div className="form-group">
						<label>Description (optional)</label>
						<textarea
							className="form-textarea"
							placeholder="What was this expense for?"
							value={description}
							onChange={(e) => setDescription(e.target.value)}
							rows={3}
						/>
					</div>

					{/* Bill Attachment */}
					<div className="form-group">
						<label>Bill / Receipt</label>
						<input
							type="file"
							ref={fileInputRef}
							onChange={handleFileChange}
							accept="image/*,.pdf"
							capture="environment"
							style={{ display: "none" }}
						/>
						<div
							className="file-upload"
							onClick={() => fileInputRef.current?.click()}
						>
							{file ? (
								<>
									<div className="upload-icon">📎</div>
									<div className="file-name">{file.name}</div>
									<div className="upload-text">
										{(file.size / 1024).toFixed(0)} KB — Tap to change
									</div>
								</>
							) : (
								<>
									<div className="upload-icon">📷</div>
									<div className="upload-text">
										Tap to take photo or choose file
									</div>
								</>
							)}
						</div>
					</div>

					{/* Submit */}
					<button
						className="btn btn-success"
						type="submit"
						disabled={submitting}
					>
						{submitting ? <span className="spinner" /> : "Submit Expense"}
					</button>
				</form>
			</div>
		</>
	);
}
