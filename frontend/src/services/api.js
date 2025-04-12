// Axios API calls go here
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5050';

export const uploadTree = (file) => {
  const formData = new FormData();
  formData.append('file', file);
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

export const getMovements = (individualId) => {
  return axios.get(`${API_BASE_URL}/movements/${individualId}`);
};
