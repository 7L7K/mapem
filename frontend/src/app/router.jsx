import { Routes, Route } from "react-router-dom";
import { lazy, Suspense } from "react";
import Layout from "@shared/components/Layout";


const Dashboard  = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage    = lazy(() => import("@features/map/pages/MapPage"));
const TimelinePage = lazy(() => import("@features/timeline/pages/TimelinePage"));
const PeoplePage = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics  = lazy(() => import("@features/analytics/pages/AnalyticsPage"));
const UploadPage = lazy(() => import("@features/upload/pages/UploadPage"));


export default function Router() {
  return (
    <Suspense fallback={<div className="text-white text-center p-8">Loading page…</div>}>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="map" element={<MapPage />} />
          <Route path="timeline" element={<TimelinePage />} />
          <Route path="people" element={<PeoplePage />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="upload" element={<UploadPage />} />
]          <Route path="*" element={<div className="p-10 text-white">404: Page Not Found</div>} />
        </Route>
      </Routes>
    </Suspense>
  );
}
