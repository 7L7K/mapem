import { useEffect, useState } from "react";

/**
 * Generic fetch hook with loading & error state.
 * Returns [data, loading, error]
 */
export default function useFetch(url, opts = {}, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    let abort = false;
    setState({ data: null, loading: true, error: null });

    fetch(url, { credentials: "include", ...opts })
      .then((res) => {
        if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
        return res.json();
      })
      .then((json) => !abort && setState({ data: json, loading: false, error: null }))
      .catch((err) => !abort && setState({ data: null, loading: false, error: err }));

    return () => {
      abort = true;
    };
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  return [state.data, state.loading, state.error];
}
