import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import {
  ArrowRightIcon,
  BookIcon,
  ExplainIcon,
  MindMapIcon,
  PracticeIcon,
  ProgressIcon,
  SeedIcon,
} from "../components/icons";
import { validateUploadFiles } from "../utils/fileValidation";

async function pollUntilReady(documentId) {
  for (let i = 0; i < 120; i++) {
    const doc = await api.documentStatus(documentId);
    if (doc.status === "ready") return doc;
    if (doc.status === "failed") throw new Error(doc.error || "Processing failed.");
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  throw new Error("Timed out waiting for the textbook to finish processing.");
}

const EXPLORE_CARDS = [
  {
    key: "explain",
    icon: ExplainIcon,
    colorClass: "c1",
    title: "Quick Explain",
    description: "Get simple explanations of any topic.",
    cta: "Start Learning",
  },
  {
    key: "practice",
    icon: PracticeIcon,
    colorClass: "c2",
    title: "Practice Zone",
    description: "Practice questions to test your understanding.",
    cta: "Try Now",
  },
  {
    key: "mindmap",
    icon: MindMapIcon,
    colorClass: "c3",
    title: "Mind Map",
    description: "Visualize and connect the concepts in your book.",
    cta: "Open",
  },
  {
    key: "progress",
    icon: ProgressIcon,
    colorClass: "c4",
    title: "Your Progress",
    description: "Track your mastery and keep growing.",
    cta: "View Progress",
  },
];

export default function Home() {
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");
  const [documents, setDocuments] = useState([]);
  const [hint, setHint] = useState("");
  const inputRef = useRef(null);
  const navigate = useNavigate();

  const refreshDocuments = useCallback(async () => {
    try {
      setDocuments(await api.documents());
    } catch {
      // seeds count / explore-card routing is non-critical
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  const handleFiles = useCallback(
    async (fileList) => {
      const validation = validateUploadFiles(fileList);
      if (!validation.ok) {
        setError(validation.error);
        return;
      }
      setError("");
      setStatus("uploading");
      try {
        const { document_id: documentId } = await api.uploadDocument(validation.files);
        setStatus("processing");
        refreshDocuments();
        await pollUntilReady(documentId);
        navigate(`/documents/${documentId}/topics`);
      } catch (err) {
        setStatus("failed");
        setError(err.message || "Upload failed.");
      }
    },
    [navigate, refreshDocuments]
  );

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleExploreCard() {
    const latestReady = documents.find((d) => d.status === "ready");
    if (!latestReady) {
      setHint("Upload a textbook first — then this will take you straight to it.");
      setTimeout(() => setHint(""), 3500);
      return;
    }
    navigate(`/documents/${latestReady.id}/topics`);
  }

  return (
    <>
      <div className="main-header">
        <h1>Upload a textbook</h1>
        <div className="seeds-badge">
          <SeedIcon />
          <strong>{documents.length}</strong> Seeds
        </div>
      </div>
      <div className="main-body">
        <div className="horizon">
          <div className="cloud c1" />
          <div className="cloud c2" />
          <div className="mountain back" />
          <div className="mountain" />
          <div className="sun" />
        </div>

        <div style={{ position: "relative", zIndex: 2 }}>
          <div className="center-col" style={{ maxWidth: 760 }}>
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
              <div>
                <BookIcon className="upload-icon-svg" />
                <h2>Drag &amp; drop your textbook here</h2>
                <p>a PDF, or photos of pages — JPG/PNG/WEBP, one or more</p>
                <button
                  type="button"
                  className="browse-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    inputRef.current?.click();
                  }}
                >
                  Browse Files
                </button>
              </div>
              <input
                ref={inputRef}
                type="file"
                accept="application/pdf,image/*"
                multiple
                style={{ display: "none" }}
                onChange={(e) => handleFiles(e.target.files)}
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

          <section className="explore">
            <div className="explore-title">Explore and learn</div>
            {hint && <div className="explore-hint">{hint}</div>}

            <div className="explore-cards">
              {EXPLORE_CARDS.map(({ key, icon: Icon, colorClass, title, description, cta }) => (
                <article key={key} className="explore-card" onClick={handleExploreCard}>
                  <div className={`explore-card-icon ${colorClass}`}>
                    <Icon />
                  </div>
                  <h2>{title}</h2>
                  <p>{description}</p>
                  <div className="explore-card-button">
                    {cta}
                    <ArrowRightIcon />
                  </div>
                </article>
              ))}
            </div>

            <footer className="explore-footer">
              <span>Your Book. Your Language. Your Understanding.</span>
            </footer>
          </section>
        </div>
      </div>
    </>
  );
}
