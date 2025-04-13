// src/App.jsx
import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard.jsx';
import UploadPanel from './components/UploadPanel.jsx';
import TreeViewer from './components/TreeViewer.jsx';
import MapView from './components/MapView.jsx';
import Timeline from './components/Timeline.jsx';
import DiffViewer from './components/DiffViewer.jsx';
import SearchPanel from './components/SearchPanel.jsx';
import SchemaViewer from './components/SchemaViewer.jsx';
import PeopleViewer from './components/PeopleViewer.jsx';
import EventPanel from './components/EventPanel.jsx';
import TreeSelector from './components/TreeSelector.jsx';
import { UploadStatusProvider } from './components/UploadStatusContext';
import UploadStatusOverlay from './components/UploadStatusOverlay';


const App = () => {
  return (
    <div className="app-container">
      <header>
        <h1>🧬 MapEm Genealogy UI</h1>
        <nav>
          <ul>
            <li><Link to="/">Dashboard</Link></li>
            <li><Link to="/upload">Upload</Link></li>
            <li><Link to="/tree">Tree</Link></li>
            <li><Link to="/map">Map</Link></li>
            <li><Link to="/timeline">Timeline</Link></li>
            <li><Link to="/diff">Diff</Link></li>
            <li><Link to="/search">Search</Link></li>
            <li><Link to="/schema">Schema</Link></li>
            <li><Link to="/people">People</Link></li>
            <li><Link to="/events">Events</Link></li>
          </ul>
        </nav>
        {/* Place the TreeSelector in the header */}
        <TreeSelector />
      </header>
      <main>
        <div style={{ color: 'limegreen', fontWeight: 'bold', padding: '1rem' }}>
          React is Rendering 🎯
        </div>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/people" element={<PeopleViewer />} />
          <Route path="/upload" element={<UploadPanel />} />
          <Route path="/tree" element={<TreeViewer />} />
          <Route path="/map" element={<MapView />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/diff" element={<DiffViewer />} />
          <Route path="/search" element={<SearchPanel />} />
          <Route path="/schema" element={<SchemaViewer />} />
          <Route path="/events" element={<EventPanel />} />
          <Route path="*" element={<div style={{ padding: '2rem' }}>Page not found.</div>} />
        </Routes>
      </main>
    </div>
  );
};

export default function WrappedApp() {
  return (
    <UploadStatusProvider>
      <UploadStatusOverlay />
      <App />
    </UploadStatusProvider>
  );
}
