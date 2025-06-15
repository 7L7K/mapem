// frontend/src/app/Providers.jsx
import React from 'react';
import axios from 'axios';
import { SearchProvider } from '@shared/context/SearchContext';
import { LegendProvider } from '@shared/context/LegendContext';
import { UploadStatusProvider } from '@shared/context/UploadStatusContext';
import { MapControlProvider } from '@shared/context/MapControlContext';

import ErrorBoundary from '@shared/components/ErrorBoundary';

let interceptorsSetup = false;

export default function Providers({ children }) {
  React.useEffect(() => {
    if (!interceptorsSetup) {
      axios.interceptors.request.use(cfg => {
        console.debug('[Axios ▶️]', cfg.method.toUpperCase(), cfg.url, cfg.data);
        return cfg;
      });
      axios.interceptors.response.use(
        res => {
          console.debug('[Axios ◀️]', res.config.url, res.status, res.data);
          return res;
        },
        err => {
          if (err.response?.status === 401) {
            if (process.env.NODE_ENV === 'development') alert('Session expired, King. Login again.');
            window.location = '/login';
          } else {
            if (process.env.NODE_ENV === 'development') alert(`[Axios❌]\n${err.config?.url}\n${err.message}`);
          }
          console.error('[Axios ❌]', err.config?.url, err.response || err.message);
          return Promise.reject(err);
        }
      );
      window.addEventListener('unhandledrejection', e => {
        console.error('🚨 UnhandledPromiseRejection', e.reason);
        if (process.env.NODE_ENV === 'development') alert(`[Promise❌] ${e.reason}`);
      });
      interceptorsSetup = true;
      if (window.DEBUG_KING_BANNER ?? process.env.NODE_ENV === 'development') {
        setTimeout(() => console.info("👑 KING MODE ENABLED! Debugging visibility maxed out."), 500);
      }
    }
  }, []);

  return (
    <ErrorBoundary>
      <UploadStatusProvider>
        <SearchProvider>
          <LegendProvider>
            <MapControlProvider>
              {children}
            </MapControlProvider>
          </LegendProvider>
        </SearchProvider>
      </UploadStatusProvider>
    </ErrorBoundary>
  );
}
