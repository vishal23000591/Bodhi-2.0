const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic"];

function isPdf(file) {
  return file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
}

function isImage(file) {
  if (file.type?.startsWith("image/")) return true;
  const name = file.name.toLowerCase();
  return IMAGE_EXTENSIONS.some((ext) => name.endsWith(ext));
}

/** Mirrors the backend's upload rule: either a single PDF, or one or more
 * photos of pages (which get combined into one multi-page document). */
export function validateUploadFiles(fileList) {
  const files = Array.from(fileList || []);
  if (files.length === 0) {
    return { ok: false, error: "No file was selected." };
  }
  if (files.length === 1 && isPdf(files[0])) {
    return { ok: true, files };
  }
  if (files.every(isImage)) {
    return { ok: true, files };
  }
  return {
    ok: false,
    error: "Upload either a single PDF, or one or more photos of pages (JPG/PNG/WEBP).",
  };
}
