import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api } from "../api/client";
import TopicCard from "../components/TopicCard";

export default function Topics() {
  const { documentId } = useParams();
  const [topics, setTopics] = useState([]);
  const [masteryMap, setMasteryMap] = useState({});
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      const data = await api.topics(documentId);
      if (cancelled) return;
      setTopics(data);
      setLoading(false);

      const entries = await Promise.all(
        data.map(async (t) => {
          try {
            return [t.id, await api.mastery(t.id)];
          } catch {
            return [t.id, null];
          }
        })
      );
      if (!cancelled) setMasteryMap(Object.fromEntries(entries));
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [documentId]);

  async function openTopic(topic) {
    const chat = await api.openChat({ document_id: documentId, topic_id: topic.id, title: topic.title });
    navigate(`/documents/${documentId}/topics/${topic.id}`, { state: { chatId: chat.id } });
  }

  return (
    <>
      <div className="main-header">
        <h1>Pick a topic</h1>
      </div>
      <div className="main-body">
        {loading && <p className="text-muted">Loading topics…</p>}
        {!loading && topics.length === 0 && (
          <div className="empty-state">No topics found for this book yet.</div>
        )}
        <div className="topic-grid">
          {topics.map((topic) => (
            <TopicCard key={topic.id} topic={topic} mastery={masteryMap[topic.id]} onClick={() => openTopic(topic)} />
          ))}
        </div>
      </div>
    </>
  );
}
