// src/index.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter as Router } from 'react-router-dom';
import App from './App.jsx';
import './styles/main.css';
import { TreeProvider } from '../context/TreeContext.jsx';


ReactDOM.createRoot(document.getElementById('root')).
 render(
     <Router>
       <TreeProvider>
         <App />
       </TreeProvider>
     </Router>
   );
  