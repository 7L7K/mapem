// frontend/src/app/main.jsx
import React, { Suspense } from "react";
import { BrowserRouter } from "react-router-dom";
import Providers from "./Providers";
import Router from "./router";
import UploadStatusOverlay from "@features/upload/components/UploadStatusOverlay";
import { ToastContainer } from 'react-toastify';
import "../shared/styles/main.css";

const App = () => (
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <Providers>
        {/* Overlays are global and always available */}
        <UploadStatusOverlay />
        <ToastContainer position="top-right" theme="dark" autoClose={3000} />

        <Suspense fallback={<div className="text-white text-center p-8">Loading MapEm...</div>}>
          <Router />
        </Suspense>
      </Providers>
    </BrowserRouter>
  </React.StrictMode>
);

export default App;
