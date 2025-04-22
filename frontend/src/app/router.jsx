import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "@shared/components/Header/Header";
import { lazy, Suspense } from "react";

const Dashboard = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage   = lazy(() => import("@features/map/pages/MapPage"));
const People    = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics = lazy(() => import("@features/analytics/pages/AnalyticsPage"));

export default function Router() {
  return (
    <BrowserRouter>
      <Header />
      <Suspense fallback={<div>Loading…</div>}>
        <Routes>
          <Route path="/"         element={<Dashboard />} />
          <Route path="/map"      element={<MapPage />} />
          <Route path="/people"   element={<People />} />
          <Route path="/analytics"element={<Analytics />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}
