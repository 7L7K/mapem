import React from "react";
import { SearchProvider } from "@shared/context/SearchContext";
import { TreeProvider } from "@shared/context/TreeContext";
import { UploadStatusProvider } from "@shared/context/UploadStatusContext.jsx";

export default function Providers({ children }) {
  return (
    <UploadStatusProvider>
      <TreeProvider>
        <SearchProvider>
          {children}
        </SearchProvider>
      </TreeProvider>
    </UploadStatusProvider>
  );
}
