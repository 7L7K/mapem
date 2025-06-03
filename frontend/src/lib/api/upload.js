export default async function uploadTree(file, onProgress = null) {
    const formData = new FormData();
    formData.append("gedcom_file", file);
    formData.append("tree_name", file.name);
  
  if (import.meta.env.DEV)
    console.log("📤 Uploading GEDCOM:", file.name, `${(file.size / 1024).toFixed(1)} KB`);
  
    try {
      const res = await fetch("http://localhost:5050/api/upload/", {
        method: "POST",
        body: formData,
      });
  
      if (!res.ok) {
        const text = await res.text();
        let trace = "";
  
        try {
          const parsed = JSON.parse(text);
          trace = parsed?.trace || "";
        } catch {
          trace = text;
        }
  
        console.error("❌ Upload failed:", res.status, trace);
        throw new Error(`Upload failed: ${res.status}\n${trace}`);
      }
  
    const data = await res.json();
    if (import.meta.env.DEV) console.log("✅ Upload successful:", data);
      return data;
    } catch (err) {
      console.error("🔥 GEDCOM Upload Error:", err);
      throw err;
    }
  }
  