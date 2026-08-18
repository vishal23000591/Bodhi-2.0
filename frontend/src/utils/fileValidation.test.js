import { describe, expect, it } from "vitest";
import { validateUploadFiles } from "./fileValidation";

function file(name, type) {
  return new File(["dummy"], name, { type });
}

describe("validateUploadFiles", () => {
  it("accepts a single PDF", () => {
    const result = validateUploadFiles([file("book.pdf", "application/pdf")]);
    expect(result.ok).toBe(true);
    expect(result.files).toHaveLength(1);
  });

  it("accepts a single photo", () => {
    const result = validateUploadFiles([file("page1.jpg", "image/jpeg")]);
    expect(result.ok).toBe(true);
  });

  it("accepts multiple photos", () => {
    const result = validateUploadFiles([
      file("page1.jpg", "image/jpeg"),
      file("page2.png", "image/png"),
      file("page3.webp", "image/webp"),
    ]);
    expect(result.ok).toBe(true);
    expect(result.files).toHaveLength(3);
  });

  it("falls back to extension when the browser doesn't set a MIME type", () => {
    const result = validateUploadFiles([file("page1.heic", "")]);
    expect(result.ok).toBe(true);
  });

  it("rejects multiple PDFs", () => {
    const result = validateUploadFiles([
      file("a.pdf", "application/pdf"),
      file("b.pdf", "application/pdf"),
    ]);
    expect(result.ok).toBe(false);
  });

  it("rejects a mix of a PDF and photos", () => {
    const result = validateUploadFiles([file("a.pdf", "application/pdf"), file("page1.jpg", "image/jpeg")]);
    expect(result.ok).toBe(false);
  });

  it("rejects unsupported file types", () => {
    const result = validateUploadFiles([file("notes.txt", "text/plain")]);
    expect(result.ok).toBe(false);
  });

  it("rejects an empty selection", () => {
    const result = validateUploadFiles([]);
    expect(result.ok).toBe(false);
  });
});
