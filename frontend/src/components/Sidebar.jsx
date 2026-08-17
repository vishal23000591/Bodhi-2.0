import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import logo from "../assets/logo.png";
import { useAuth } from "../context/AuthContext";
import { groupChatsByRecency } from "../utils/dateGroups";

export default function Sidebar() {
  const [chats, setChats] = useState([]);
  const [search, setSearch] = useState("");
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { topicId } = useParams();

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    try {
      setChats(await api.chats());
    } catch {
      // sidebar history is non-critical; fail silently
    }
  }

  async function handleDelete(e, chatId) {
    e.stopPropagation();
    e.preventDefault();
    if (!window.confirm("Delete this chat?")) return;
    await api.deleteChat(chatId);
    refresh();
  }

  const filtered = useMemo(
    () => chats.filter((c) => c.title.toLowerCase().includes(search.toLowerCase())),
    [chats, search]
  );
  const groups = useMemo(() => groupChatsByRecency(filtered), [filtered]);

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
            No chats yet
          </p>
        )}
        {groups.map(([label, items]) => (
          <div key={label}>
            <div className="sidebar-group-label">{label}</div>
            {items.map((chat) => (
              <Link
                key={chat.id}
                to={`/documents/${chat.document_id}/topics/${chat.topic_id}`}
                className={`sidebar-item ${topicId === chat.topic_id ? "active" : ""}`}
              >
                <span>📄</span>
                <span className="sidebar-item-title">{chat.title}</span>
                <button className="sidebar-item-delete" onClick={(e) => handleDelete(e, chat.id)}>
                  ✕
                </button>
              </Link>
            ))}
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
