// frontend/src/components/Layout.jsx
import React, { useEffect } from "react";
import Header from "./Header";

export default function Layout({ children }) {
  useEffect(() => {
    console.log("🏗️ [Layout.jsx] Layout mounted");
    console.log("📦 [Layout.jsx] Children received:", children?.type?.name || typeof children);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-900 text-white flex flex-col">
      <Header />
      <main className="flex-1 pt-6 px-6">
        {children}
      </main>
    </div>
  );
}
