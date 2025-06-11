/**
 * downloadFile(filename, data, mimeType)
 * Utility to trigger a client-side “Save As…” download
 */
export function downloadFile(filename, data, contentType = "application/octet-stream") {
  const blob = data instanceof Blob ? data : new Blob([data], { type: contentType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
