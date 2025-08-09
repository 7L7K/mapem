import { client } from './api';

export default async function uploadTree(file, onProgress = null) {
  const formData = new FormData();
  formData.append('gedcom_file', file);
  formData.append('tree_name', file.name);

  if (import.meta.env.DEV) {
    console.log('📤 Uploading GEDCOM:', file.name, `${(file.size / 1024).toFixed(1)} KB`);
  }

  try {
    const res = await client.post('/api/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: onProgress ?? undefined,
    });
    if (import.meta.env.DEV) console.log('✅ Upload successful:', res.data);
    return res.data;
  } catch (err) {
    console.error('🔥 GEDCOM Upload Error:', err);
    throw err;
  }
}
