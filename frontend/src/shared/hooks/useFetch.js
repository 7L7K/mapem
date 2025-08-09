import { useState, useEffect, useRef } from 'react';

// KingMode: use window.DEBUG_FETCH = true to go ultra verbose in dev!
// Deprecated: prefer React Query
export function useFetch(url, options = {}, { verbose } = {}) {
  const isMounted = useRef(true);
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => () => { isMounted.current = false; }, []);

  const fetchData = async () => {
    setLoading(true);
    const v = verbose ?? window.DEBUG_FETCH ?? false;
    const reqId = (Math.random() + 1).toString(36).substring(7);
    if (v) console.group(`🟢 [fetch ▶️] ${url} [req:${reqId}]`);
    try {
      const res = await fetch(url, options);
      const clone = res.clone();
      const text = await clone.text();
      if (v || !res.ok) {
        console.log('Request:', { url, options });
        console.log('Response:', {
          status: res.status,
          headers: Object.fromEntries(res.headers.entries()),
          body: text,
          requestId: reqId,
        });
      }
      if (!res.ok) throw new Error(`HTTP ${res.status} [req:${reqId}]`);
      const json = await res.json();
      if (isMounted.current) setData(json);
      if (v) console.groupEnd();
    } catch (err) {
      if (isMounted.current) setError(err);
      if (v || process.env.NODE_ENV === 'development') {
        alert(`[fetch❌] ${url}\n\n${err}`);
      }
      console.error(`[fetch❌] ${url} [req:${reqId}]`, err);
      if (v) console.groupEnd();
    } finally {
      if (isMounted.current) setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [url]);

  return { data, error, loading, refetch: fetchData };
}

export default useFetch;
