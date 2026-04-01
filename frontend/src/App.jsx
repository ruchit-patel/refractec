import { FrappeProvider } from "frappe-react-sdk";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./index.css";
import Login from "./pages/Login";
import Home from "./pages/Home";
import Attendance from "./pages/Attendance";
import Overtime from "./pages/Overtime";
import Expense from "./pages/Expense";
import Advance from "./pages/Advance";

function App() {
	return (
		<FrappeProvider>
			<BrowserRouter basename="/frontend">
				<Routes>
					<Route path="/login" element={<Login />} />
					<Route path="/" element={<Home />} />
					<Route path="/attendance" element={<Attendance />} />
					<Route path="/overtime" element={<Overtime />} />
					<Route path="/expense" element={<Expense />} />
					<Route path="/advance" element={<Advance />} />
					<Route path="*" element={<Navigate to="/" replace />} />
				</Routes>
			</BrowserRouter>
		</FrappeProvider>
	);
}

export default App;
