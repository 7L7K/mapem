// frontend/src/app/router.jsx
import { Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { lazy, Suspense, useEffect } from "react";
import ErrorBoundary from "@shared/components/ErrorBoundary";
import Layout from "@shared/components/Layout";
import { useTree } from "@shared/context/TreeContext";  // <-- new
import { routes as routeConfig } from './routes.config';

const Dashboard = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage = lazy(() => import("@features/map/pages/MapPage"));
const TimelinePage = lazy(() => import("@features/timeline/pages/TimelinePage"));
const PeoplePage = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics = lazy(() => import("@features/analytics/pages/AnalyticsPage"));
const UploadPage = lazy(() => import("@features/upload/pages/UploadPage"));
const GeocodeDashboardPage = lazy(() => import("@features/geocode/pages/GeocodeDashboardPage"))


/* Tiny helper so /map can still work */
function MapAutoRedirect() {
  const { allTrees } = useTree();
  const navigate = useNavigate();

  useEffect(() => {
    if (allTrees.length) {
      navigate(`/map/${allTrees[0].uploaded_tree_id}`, { replace: true });
    } else {
      // No trees yet → send to upload page to get started
      navigate('/upload', { replace: true });
    }
  }, [allTrees, navigate]);

  return <div className="p-6 text-white">Loading Map…</div>;
}

export default function Router() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<div className="text-white text-center p-8">Loading page…</div>}>
        <Routes>
          <Route path="/" element={<Layout />}>
            {/* Index route */}
            <Route index element={<Dashboard />} />

            {/* Declarative routes from centralized config */}
            {routeConfig.filter(r => !r.isIndex).map(({ path, component: Component }) => (
              <Route key={path} path={path.replace(/^\//, '')} element={<Component />} />
            ))}

            {/* Legacy /map -> latest */}
            <Route path="map" element={<MapAutoRedirect />} />

            {/* 404 */}
            <Route path="*" element={<div className="p-10 text-white">404: Page Not Found</div>} />
          </Route>
        </Routes>
      </Suspense>
    </ErrorBoundary>
  );
}
