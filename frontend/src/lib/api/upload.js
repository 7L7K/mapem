export default async function uploadTree(file, onProgress = null) {
    const formData = new FormData();
    formData.append("file", file);
  
    console.log("📤 Uploading GEDCOM:", file.name, `${(file.size / 1024).toFixed(1)} KB`);
  
    try {
      const res = await fetch("/api/upload/", {
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
      console.log("✅ Upload successful:", data);
      return data;
    } catch (err) {
      console.error("🔥 GEDCOM Upload Error:", err);
      throw err;
    }
  }
  