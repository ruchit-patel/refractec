import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useFrappeAuth } from "frappe-react-sdk";
import Toast from "../components/Toast";

export default function Login() {
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [submitting, setSubmitting] = useState(false);
	const [toast, setToast] = useState(null);
	const navigate = useNavigate();
	const { login, currentUser } = useFrappeAuth();

	// If already logged in, redirect
	if (currentUser && currentUser !== "Guest") {
		navigate("/", { replace: true });
		return null;
	}

	const handleLogin = async (e) => {
		e.preventDefault();
		if (!email || !password) {
			setToast({ message: "Please enter email and password", type: "error" });
			return;
		}
		setSubmitting(true);
		try {
			await login({ username: email, password });
			navigate("/", { replace: true });
		} catch (err) {
			setToast({
				message: err?.message || "Invalid credentials",
				type: "error",
			});
		} finally {
			setSubmitting(false);
		}
	};

	return (
		<div className="login-container">
			{toast && (
				<Toast
					message={toast.message}
					type={toast.type}
					onClose={() => setToast(null)}
				/>
			)}
			<form className="login-card" onSubmit={handleLogin}>
				<h1>Refractec</h1>
				<p className="login-subtitle">Supervisor Login</p>

				<div className="form-group">
					<label>Email</label>
					<input
						className="form-input"
						type="email"
						placeholder="you@example.com"
						value={email}
						onChange={(e) => setEmail(e.target.value)}
						autoComplete="username"
						autoFocus
					/>
				</div>

				<div className="form-group">
					<label>Password</label>
					<input
						className="form-input"
						type="password"
						placeholder="Enter password"
						value={password}
						onChange={(e) => setPassword(e.target.value)}
						autoComplete="current-password"
					/>
				</div>

				<button className="btn btn-primary" type="submit" disabled={submitting}>
					{submitting ? <span className="spinner" /> : "Login"}
				</button>
			</form>
		</div>
	);
}
