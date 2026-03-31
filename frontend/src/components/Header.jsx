import { useNavigate } from "react-router-dom";

export default function Header({ title, subtitle, showBack = false }) {
	const navigate = useNavigate();

	return (
		<div className="app-header">
			{showBack && (
				<button className="back-btn" onClick={() => navigate("/")}>
					&#8592;
				</button>
			)}
			<div>
				<h1>{title}</h1>
				{subtitle && <div className="subtitle">{subtitle}</div>}
			</div>
		</div>
	);
}
