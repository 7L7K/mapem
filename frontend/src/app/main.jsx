// frontend/src/app/main.jsx
import React, { Suspense } from "react";
import { BrowserRouter } from "react-router-dom";
import Providers from "./Providers";
import Router from "./router";
import UploadStatusOverlay from "@features/upload/components/UploadStatusOverlay";
import "../shared/styles/main.css";



const App = () => (
  <React.StrictMode>
    <BrowserRouter>
      <Providers>
        {/* Overlay is global and always available */}
        <UploadStatusOverlay />

        <Suspense fallback={<div className="text-white text-center p-8">Loading MapEm...</div>}>
          <Router />
        </Suspense>
      </Providers>
    </BrowserRouter>
  </React.StrictMode>
);

export default App;
