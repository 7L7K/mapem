// frontend/src/features/geocode/components/FixModal.jsx
import React, { useState, useEffect } from "react";
import ReactDOM from "react-dom";
import PropTypes from "prop-types";
import axios from "axios";
import { MapContainer, TileLayer, Marker } from "react-leaflet";
import { devLog } from "@shared/utils/devLogger";

export default function FixModal({ isOpen, onClose, locationId, onSuccess }) {
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [errors, setErrors] = useState({});
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      setLat("");
      setLng("");
      setErrors({});
      setShowPreview(false);
    }
  }, [isOpen]);

  const validate = () => {
    const errs = {};
    const numLat = parseFloat(lat);
    const numLng = parseFloat(lng);
    if (!/^[-+]?\d*\.?\d+$/.test(lat)) errs.lat = "Invalid format";
    else if (numLat < -90 || numLat > 90) errs.lat = "Must be between -90 and 90";
    if (!/^[-+]?\d*\.?\d+$/.test(lng)) errs.lng = "Invalid format";
    else if (numLng < -180 || numLng > 180)
      errs.lng = "Must be between -180 and 180";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handlePreview = () => {
    if (validate()) setShowPreview(true);
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    const reqId = Math.random().toString(36).slice(2);
    devLog("FixModal", `🛠️ [${reqId}] Submitting fix for ${locationId}`, {
      lat,
      lng,
    });
    try {
      await axios.post(`/admin/geocode/fix/${locationId}`, { lat, lng });
      devLog("FixModal", `✅ [${reqId}] Fix submitted`);
      alert(`Fix submitted (req: ${reqId})`);
      onSuccess();
      onClose();
    } catch (err) {
      devLog("FixModal", `❌ [${reqId}] Submit error`, err);
      alert("Error submitting fix");
    }
  };

  if (!isOpen) return null;

  return ReactDOM.createPortal(
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Manual Fix for ID {locationId}</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium">Latitude</label>
            <input
              type="text"
              value={lat}
              onChange={e => setLat(e.target.value)}
              onBlur={validate}
              className="mt-1 block w-full border rounded p-2"
            />
            {errors.lat && <p className="text-red-500 text-sm">{errors.lat}</p>}
          </div>
          <div>
            <label className="block text-sm font-medium">Longitude</label>
            <input
              type="text"
              value={lng}
              onChange={e => setLng(e.target.value)}
              onBlur={validate}
              className="mt-1 block w-full border rounded p-2"
            />
            {errors.lng && <p className="text-red-500 text-sm">{errors.lng}</p>}
          </div>
          <div className="flex space-x-2">
            <button
              onClick={handlePreview}
              className="px-4 py-2 bg-gray-200 rounded"
            >
              Preview
            </button>
            <button
              onClick={handleSubmit}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              Submit Fix
            </button>
            <button
              onClick={() => {
                devLog("FixModal", "✖️ Cancel clicked");
                onClose();
              }}
              className="px-4 py-2 bg-red-600 text-white rounded"
            >
              Cancel
            </button>
          </div>
        </div>
        {showPreview && (
          <div className="mt-4 h-64">
            <MapContainer
              center={[parseFloat(lat), parseFloat(lng)]}
              zoom={13}
              style={{ height: "100%", width: "100%" }}
            >
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <Marker position={[parseFloat(lat), parseFloat(lng)]} />
            </MapContainer>
          </div>
        )}
      </div>
    </div>,
    document.body
  );
}

FixModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  locationId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  onSuccess: PropTypes.func.isRequired,
};
