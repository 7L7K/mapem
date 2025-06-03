import { useState } from "react";
export default function useLocalStorage(key, defaultVal) {
  const [val, setVal] = useState(() => {
    try { return JSON.parse(localStorage.getItem(key)) ?? defaultVal; }
    catch { return defaultVal; }
  });
  return [val, v => { setVal(v); localStorage.setItem(key, JSON.stringify(v)); }];
}
