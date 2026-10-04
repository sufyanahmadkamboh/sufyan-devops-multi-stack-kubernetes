import { useCallback, useEffect, useState } from "react";

// Fetch JSON from a relative URL. On failure the panel says which service is unreachable, and why.
export function useApi(url, service) {
  const [state, setState] = useState({ loading: true, data: null, error: null });
  const load = useCallback(async () => {
    try {
      const res = await fetch(url, { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setState({ loading: false, data: await res.json(), error: null });
    } catch (err) {
      setState({ loading: false, data: null, error: `${service} unreachable: ${err.message}` });
    }
  }, [url, service]);
  useEffect(() => {
    load();
  }, [load]);
  return { ...state, reload: load };
}
