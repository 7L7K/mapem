///Users/kingal/mapem/frontend/src/App.jsx
import React, { useEffect } from "react";
import { Routes, Route, useLocation } from "react-router-dom";

import Dashboard from "./components/Dashboard.jsx";
import UploadPanel from "./components/UploadPanel.jsx";
import TreeViewer from "./components/TreeViewer.jsx";
import MapView from "./components/MapView.jsx";
import Timeline from "./components/Timeline.jsx";
import DiffViewer from "./components/DiffViewer.jsx";
import SearchPanel from "./components/SearchPanel.jsx";
import SchemaViewer from "./components/SchemaViewer.jsx";
import PeopleViewer from "./components/PeopleViewer.jsx";
import EventPanel from "./components/EventPanel.jsx";
import AnalyticsPage from "./views/Analytics.jsx";

import Header from "./components/Header.jsx";
import UploadStatusOverlay from "./components/UploadStatusOverlay.jsx";
import { UploadStatusProvider } from "./components/UploadStatusContext";

import "./styles/Layout.css";

const AppRoutes = () => {
  const loc = useLocation();
  useEffect(() => {
    console.log("🛣️ [Router] navigated ➜", loc.pathname);
  }, [loc.pathname]);

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/upload" element={<UploadPanel />} />
      <Route path="/tree" element={<TreeViewer />} />
      <Route path="/map" element={<MapView />} />
      <Route path="/timeline" element={<Timeline />} />
      <Route path="/diff" element={<DiffViewer />} />
      <Route path="/search" element={<SearchPanel />} />
      <Route path="/schema" element={<SchemaViewer />} />
      <Route path="/people" element={<PeopleViewer />} />
      <Route path="/events" element={<EventPanel />} />
      <Route path="/analytics" element={<AnalyticsPage />} />
      <Route
        path="*"
        element={<div className="p-6 text-white">Page not found.</div>}
      />
    </Routes>
  );
};

const App = () => (
  <div className="bg-black min-h-screen text-white">
    <Header />
    <main className="pt-6 px-6">
      <AppRoutes />
    </main>
  </div>
);

export default function WrappedApp() {
  return (
    <UploadStatusProvider>
      <UploadStatusOverlay />
      <App />
    </UploadStatusProvider>
  );
}
