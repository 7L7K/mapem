// src/components/geocode/BatchControls.jsx
import React, { useState } from 'react';
import { downloadFile } from "@shared/utils/download";
import { toast } from 'react-toastify';
import geoApi from '@api/geocodeApi';

const { exportData, runFuzzyMatch, retryAll } = geoApi;

export default function BatchControls({ onActionComplete }) {
  const [loading, setLoading] = useState(false);

  const handleAction  = async (actionFn, successMsg, isDestructive = false) => {
    if (isDestructive && !window.confirm('Are you sure?')) return;
    try {
      setLoading(true);
      const res = await actionFn();
      // if CSV, res.data is Blob
      if (actionFn === exportData) {
        const format = res.config.params.format;
        downloadFile(`geocode_export.${format}`, res.data, res.headers['content-type']);
      } else {
        toast.success(successMsg);
      }
      onActionComplete();
    } catch (err) {
      console.error(err);
      toast.error(err.response?.data?.message || 'Action failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex space-x-4">
      <button
        className="btn"
        disabled={loading}
        onClick={() => handleAction(retryAll, 'All retries queued', true)}
      >
        Retry All
      </button>

      <button
        className="btn"
        disabled={loading}
        onClick={() => handleAction(runFuzzyMatch, 'Fuzzy match complete')}
      >
        Run Fuzzy Match
      </button>

      <div className="relative">
        <button className="btn" disabled={loading}>
          Export…
        </button>
        <div className="absolute right-0 mt-2 w-32 bg-white text-black shadow-lg">
          {['json','csv'].map(fmt => (
            <div
              key={fmt}
              className="px-4 py-2 hover:bg-gray-200 cursor-pointer"
              onClick={() => handleAction(() => exportData(fmt), `Exported ${fmt.toUpperCase()}`)}
            >
              {fmt.toUpperCase()}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
