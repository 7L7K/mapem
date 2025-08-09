// Centralized route configuration for better maintainability
import { lazy } from "react";

// Lazy load all page components
const Dashboard = lazy(() => import("@features/dashboard/pages/DashboardPage"));
const MapPage = lazy(() => import("@features/map/pages/MapPage"));
const TimelinePage = lazy(() => import("@features/timeline/pages/TimelinePage"));
const PeoplePage = lazy(() => import("@features/people/pages/PeoplePage"));
const Analytics = lazy(() => import("@features/analytics/pages/AnalyticsPage"));
const UploadPage = lazy(() => import("@features/upload/pages/UploadPage"));
const GeocodeDashboardPage = lazy(() => import("@features/geocode/pages/GeocodeDashboardPage"));

export const routes = [
    {
        path: "/",
        component: Dashboard,
        title: "Dashboard",
        isIndex: true
    },
    {
        path: "/dashboard",
        component: Dashboard,
        title: "Dashboard"
    },
    {
        path: "/map/:treeId",
        component: MapPage,
        title: "Map",
        params: ["treeId"]
    },
    {
        path: "/timeline",
        component: TimelinePage,
        title: "Timeline"
    },
    {
        path: "/people",
        component: PeoplePage,
        title: "People"
    },
    {
        path: "/analytics",
        component: Analytics,
        title: "Analytics"
    },
    {
        path: "/upload",
        component: UploadPage,
        title: "Upload"
    },
    {
        path: "/geocode",
        component: GeocodeDashboardPage,
        title: "Geocode Dashboard"
    }
];

// Navigation items for header/sidebar
export const navItems = routes
    .filter(route => !route.isIndex && !route.params)
    .map(route => ({
        path: route.path,
        title: route.title
    }));
