// src/app/Providers.jsx
import React from "react";
import { SearchProvider } from "@shared/context/SearchContext";
import { TreeProvider } from "@shared/context/TreeContext";
import { UploadStatusProvider } from "@shared/context/UploadStatusContext";
import { MapControlProvider } from "@shared/context/MapControlContext";
import { LegendProvider } from "@shared/context/LegendContext";

export default function Providers({ children }) {
  return (
    <UploadStatusProvider>
      <TreeProvider>
        <SearchProvider>
          <MapControlProvider>
            <LegendProvider>
              {children}
            </LegendProvider>
          </MapControlProvider>
        </SearchProvider>
      </TreeProvider>
    </UploadStatusProvider>
  );
}
