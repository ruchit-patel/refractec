import { useState, useEffect, useCallback } from "react";
import { useFrappeAuth, useFrappePostCall } from "frappe-react-sdk";

export function useSupervisor() {
	const { currentUser, isLoading: authLoading } = useFrappeAuth();
	const [context, setContext] = useState(null);
	const [loading, setLoading] = useState(true);
	const [error, setError] = useState(null);

	const { call: fetchContext } = useFrappePostCall(
		"refractec.api.get_supervisor_context"
	);

	const loadContext = useCallback(async () => {
		if (!currentUser || currentUser === "Guest") {
			setLoading(false);
			return;
		}
		try {
			setLoading(true);
			setError(null);
			const res = await fetchContext({});
			setContext(res.message);
		} catch (err) {
			setError(err?.message || "Failed to load supervisor data");
		} finally {
			setLoading(false);
		}
	}, [currentUser, fetchContext]);

	useEffect(() => {
		if (!authLoading && currentUser && currentUser !== "Guest") {
			loadContext();
		} else if (!authLoading) {
			setLoading(false);
		}
	}, [authLoading, currentUser, loadContext]);

	return {
		currentUser,
		authLoading,
		context,
		loading,
		error,
		reload: loadContext,
	};
}
