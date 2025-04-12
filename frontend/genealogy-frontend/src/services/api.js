// src/services/api.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

export const uploadTree = (file) => {
  const formData = new FormData();
  formData.append('gedcom_file', file);          // fix key name
  formData.append('tree_name', file.name);       // required by Flask
  formData.append('uploader_name', 'King');      // optional but matches backend
  return axios.post(`${API_BASE_URL}/upload_tree`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const getTree = (treeId) => {
  return axios.get(`${API_BASE_URL}/tree/${treeId}`);
};

export const compareTrees = (newId, existingId) => {
  return axios.get(`${API_BASE_URL}/compare_trees`, {
    params: { new_id: newId, existing_id: existingId }
  });
};

export const search = (query) => {
  return axios.get(`${API_BASE_URL}/search`, { params: { q: query } });
};

export const getMovements = (treeId) => {
  return axios.get(`${API_BASE_URL}/api/movements/${treeId}`).then(res => res.data);
};

export const getPeople = (treeId) => {
  return axios.get(`${API_BASE_URL}/api/people`, { params: { tree_id: treeId } }).then(res => res.data);
};

export const getEvents = (treeId) => {
  return axios.get(`${API_BASE_URL}/api/events`, { params: { tree_id: treeId } }).then(res => res.data);
};

export const getTimeline = (treeId) => {
  return axios.get(`${API_BASE_URL}/api/timeline/${treeId}`).then(res => res.data);
};

export const getSchema = () => {
  return axios.get(`${API_BASE_URL}/api/schema`).then(res => res.data);
};
