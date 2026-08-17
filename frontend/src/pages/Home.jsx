import { useCallback, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

async function pollUntilReady(documentId) {
  for (let i = 0; i < 120; i++) {
    const doc = await api.documentStatus(documentId);
    if (doc.status === "ready") return doc;
    if (doc.status === "failed") throw new Error(doc.error || "Processing failed.");
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error("Timed out waiting for the textbook to finish processing.");
}

export default function Home() {
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const handleFile = useCallback(
    async (file) => {
      if (!file) return;
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError("Please upload a PDF file.");
        return;
      }
      setError("");
      setStatus("uploading");
      try {
        const { document_id: documentId } = await api.uploadDocument(file);
        setStatus("processing");
        await pollUntilReady(documentId);
        navigate(`/documents/${documentId}/topics`);
      } catch (err) {
        setStatus("failed");
        setError(err.message || "Upload failed.");
      }
    },
    [navigate]
  );

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <>
      <div className="main-header">
        <h1>Upload a textbook</h1>
      </div>
      <div className="main-body">
        <div className="center-col">
          <div
            className={`upload-box ${dragging ? "dragging" : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <div className="upload-icon">📚</div>
            <h2>Drop your textbook here</h2>
            <p>or click to browse — PDF only</p>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              style={{ display: "none" }}
              onChange={(e) => handleFile(e.target.files?.[0])}
            />
          </div>

          {error && (
            <div className="form-error" style={{ marginTop: 16 }}>
              {error}
            </div>
          )}

          {(status === "uploading" || status === "processing") && (
            <div className="upload-status">
              <div className="spinner" />
              {status === "uploading" ? "Uploading…" : "Reading your textbook and building topics…"}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
