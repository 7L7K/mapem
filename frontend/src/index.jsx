import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import WrappedApp from './App.jsx';  // 👈 this includes all the providers
import './styles/main.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <WrappedApp />
    </BrowserRouter>
  </React.StrictMode>
);
