import React from "react";
import Header from "./Header";

export default function Layout({ children }) {
  return (
    <div className="bg-background text-text min-h-screen flex flex-col">
      {/* Sticky Header */}
      <Header />

      {/* Main Content Area */}
      <main className="flex-1 overflow-hidden">
        {children}
      </main>
    </div>
  );
}
