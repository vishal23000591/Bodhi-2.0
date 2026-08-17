import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import logo from "../assets/logo.png";
import { useAuth } from "../context/AuthContext";
import { groupByRecency } from "../utils/dateGroups";

function displayName(filename) {
  return (filename || "Untitled").replace(/\.pdf$/i, "");
}

export default function Sidebar() {
  const [documents, setDocuments] = useState([]);
  const [chats, setChats] = useState([]);
  const [topicsByDocId, setTopicsByDocId] = useState({});
  const [expanded, setExpanded] = useState(new Set());
  const [search, setSearch] = useState("");
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { documentId, topicId } = useParams();

  const refresh = useCallback(async () => {
    try {
      const [docs, chatList] = await Promise.all([api.documents(), api.chats()]);
      setDocuments(docs);
      setChats(chatList);
    } catch {
      // sidebar history is non-critical; fail silently
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, documentId, topicId]);

  const ensureTopicsLoaded = useCallback(async (docId) => {
    try {
      const topics = await api.topics(docId);
      setTopicsByDocId((prev) => ({ ...prev, [docId]: topics }));
    } catch {
      // non-critical — the document row still works without its topic list
    }
  }, []);

  // Keep the book you're currently reading expanded, and make sure its
  // topics (needed both for navigation state and the "already chatted"
  // sub-branch styling) are loaded.
  useEffect(() => {
    if (!documentId) return;
    setExpanded((prev) => (prev.has(documentId) ? prev : new Set(prev).add(documentId)));
    if (!topicsByDocId[documentId]) ensureTopicsLoaded(documentId);
  }, [documentId, ensureTopicsLoaded, topicsByDocId]);

  function toggleExpand(docId) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(docId)) next.delete(docId);
      else next.add(docId);
      return next;
    });
    if (!topicsByDocId[docId]) ensureTopicsLoaded(docId);
  }

  async function handleDeleteTopicChat(e, chatId) {
    e.stopPropagation();
    e.preventDefault();
    if (!window.confirm("Delete this chat?")) return;
    await api.deleteChat(chatId);
    refresh();
  }

  async function handleDeleteDocument(e, docId) {
    e.stopPropagation();
    e.preventDefault();
    if (!window.confirm("Delete this textbook and all of its chat history? This can't be undone.")) return;
    await api.deleteDocument(docId);
    if (documentId === docId) navigate("/");
    refresh();
  }

  const chatByTopicId = useMemo(() => Object.fromEntries(chats.map((c) => [c.topic_id, c])), [chats]);

  const query = search.trim().toLowerCase();
  const isSearching = query.length > 0;

  // While searching, load every document's topics so titles are searchable
  // too, not just filenames.
  useEffect(() => {
    if (!isSearching) return;
    documents.forEach((d) => {
      if (!topicsByDocId[d.id]) ensureTopicsLoaded(d.id);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isSearching, documents]);

  const visibleDocuments = useMemo(() => {
    if (!isSearching) return documents;
    return documents.filter((d) => {
      const filenameMatch = displayName(d.filename).toLowerCase().includes(query);
      const topics = topicsByDocId[d.id] || [];
      const topicMatch = topics.some((t) => t.title.toLowerCase().includes(query));
      return filenameMatch || topicMatch;
    });
  }, [documents, isSearching, query, topicsByDocId]);

  function topicsToRender(doc) {
    const topics = topicsByDocId[doc.id] || [];
    if (!isSearching) return topics;
    const filenameMatch = displayName(doc.filename).toLowerCase().includes(query);
    if (filenameMatch) return topics;
    return topics.filter((t) => t.title.toLowerCase().includes(query));
  }

  const groups = useMemo(
    () => groupByRecency(visibleDocuments, (d) => d.created_at),
    [visibleDocuments]
  );

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <img src={logo} alt="Bodhi" />
        BODHI
      </div>

      <button className="btn-new-chat" onClick={() => navigate("/")}>
        + New chat
      </button>

      <div className="sidebar-search">
        🔍
        <input placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} />
      </div>

      <div className="sidebar-groups">
        {groups.length === 0 && (
          <p className="text-muted" style={{ padding: "0 8px", fontSize: "0.85rem" }}>
            {isSearching ? "No matches" : "No textbooks yet"}
          </p>
        )}
        {groups.map(([label, docs]) => (
          <div key={label}>
            <div className="sidebar-group-label">{label}</div>
            {docs.map((doc) => {
              const isOpen = isSearching || expanded.has(doc.id);
              const topics = topicsToRender(doc);
              return (
                <div key={doc.id}>
                  <div
                    className={`sidebar-doc-item ${documentId === doc.id ? "active" : ""}`}
                    onClick={() => toggleExpand(doc.id)}
                  >
                    <span className={`sidebar-doc-chevron ${isOpen ? "open" : ""}`}>▸</span>
                    <span>📚</span>
                    <Link
                      to={`/documents/${doc.id}/topics`}
                      className="sidebar-item-title"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {displayName(doc.filename)}
                    </Link>
                    {doc.status === "processing" && <span className="sidebar-doc-status">Processing…</span>}
                    {doc.status === "failed" && <span className="sidebar-doc-status failed">Failed</span>}
                    <button
                      className="sidebar-item-delete"
                      onClick={(e) => handleDeleteDocument(e, doc.id)}
                    >
                      ✕
                    </button>
                  </div>
                  {isOpen && (
                    <div className="sidebar-topic-list">
                      {topics.length === 0 && doc.status === "ready" && (
                        <div className="sidebar-topic-empty">No topics yet</div>
                      )}
                      {topics.map((topic) => {
                        const chat = chatByTopicId[topic.id];
                        const chatted = Boolean(chat);
                        return (
                          <Link
                            key={topic.id}
                            to={`/documents/${doc.id}/topics/${topic.id}`}
                            className={`sidebar-item sidebar-topic-item ${chatted ? "chatted" : "not-chatted"} ${
                              topicId === topic.id ? "active" : ""
                            }`}
                          >
                            <span>{chatted ? "💬" : "📄"}</span>
                            <span className="sidebar-item-title">{topic.title}</span>
                            {chatted && (
                              <button
                                className="sidebar-item-delete"
                                onClick={(e) => handleDeleteTopicChat(e, chat.id)}
                              >
                                ✕
                              </button>
                            )}
                          </Link>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>

      <div className="sidebar-profile">
        <div className="sidebar-avatar">{(user?.name || "?").slice(0, 1).toUpperCase()}</div>
        <span>{user?.name}</span>
        <button className="sidebar-logout" onClick={logout}>
          Log out
        </button>
      </div>
    </aside>
  );
}
