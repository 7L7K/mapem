// /frontend/src/lib/api/api.js
import axios from 'axios';
import qs from 'qs';
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050';

// ─── low‑level axios instance ───────────────────────────────────────────────
export const client = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
});

client.interceptors.response.use(
  res => res,
  err => {
    console.warn('🔥 AXIOS ERROR', {
      url: err.config?.url,
      status: err.response?.status,
      data: err.response?.data,
    })
    return Promise.reject(err)
  }
)

const ok = (p) => p.then((r) => r.data);

// ─── uploads ────────────────────────────────────────────────────────────────
export const uploadTree = (file) => {
  const formData = new FormData();
  formData.append('gedcom_file', file);
  formData.append('tree_name', file.name);
  formData.append('uploader_name', 'King');
  return ok(
    client.post('/api/upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  );
};

// ─── trees ──────────────────────────────────────────────────────────────────
export const getTrees = () =>
  client.get('/api/trees/')
    .then(res => {
      const data = res?.data;
      const rawTrees = Array.isArray(data?.trees) ? data.trees : [];

      if (!rawTrees.length && import.meta.env.DEV) {
        console.warn("⚠️ getTrees(): No trees returned or wrong shape:", data);
      }

      return rawTrees.map(tree => ({
        id: tree.uploaded_tree_id ?? tree.tree_id ?? tree.id ?? "unknown",
        uploaded_tree_id: tree.uploaded_tree_id ?? tree.id ?? null,
        version_number: tree.version_number ?? 1,
        name: tree.tree_name ?? tree.name ?? "Untitled",
        created_at: tree.created_at ?? null,
      }));
    })
    .catch(err => {
      console.error("❌ [getTrees] failed:", err);
      return [];
    });

export const getTree         = (id)                       => ok(client.get(`/api/trees/${id}`));
export const getTreeCounts = (uploadedTreeId) =>
  ok(client.get(`/api/trees/${uploadedTreeId}/uploaded-counts`));
export const getVisibleCounts = (id, filters) =>
  ok(client.get(`/api/trees/${id}/visible-counts`, {
    params: filters,
    paramsSerializer: p => qs.stringify(p, { arrayFormat: 'repeat', skipNulls: true }),
  }));

// ─── people / events ────────────────────────────────────────────────────────
export const getPeople   = (treeId, limit = 100, offset = 0) =>
  ok(client.get(`/api/people/${treeId}`, { params: { limit, offset } }));
export const getEvents   = (treeId, limit = 100, offset = 0) =>
  ok(client.get(`/api/events/${treeId}`, { params: { limit, offset } }));
export const searchPeople = (q)                            => ok(client.get('/api/people/search', { params: { q } }));
export const getRelatives = (personId, types)              =>
  ok(client.get(`/api/people/${personId}/relatives`, { params: { types: types.join(',') } }));
export const getHousehold = (personId, year)               =>
  ok(client.get(`/api/people/${personId}/household`, { params: { year } }));

// ─── movements / timeline ───────────────────────────────────────────────────
export const getMovements = (treeId, filters = {}) =>
  ok(client.get(`/api/movements/${treeId}`, {
    params: filters,
    paramsSerializer: p => qs.stringify(p, { arrayFormat: 'repeat', skipNulls: true }),
  }));

export const getFamilyMovements = (treeId, familyId, filters = {}) =>
  getMovements(treeId, { ...filters, familyId, grouped: 'family' });

export const getGroupMovements = (treeId, personIds = [], filters = {}) =>
  getMovements(treeId, { ...filters, personIds: personIds.join(','), grouped: 'person' });
export const getTimeline  = (treeId)  => ok(client.get(`/api/timeline/${treeId}`));
export const getSchema    = ()        => ok(client.get('/api/schema'));

// ─── misc search / compare ──────────────────────────────────────────────────
export const search       = (q)                          => ok(client.get('/api/search', { params: { q } }));
export const compareTrees = (newId, existingId)          =>
  ok(client.get('/api/compare_trees', { params: { new_id: newId, existing_id: existingId } }));

export { AxiosError } from 'axios';
