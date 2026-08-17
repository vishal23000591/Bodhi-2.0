import MasteryBadge from "./MasteryBadge";

export default function TopicCard({ topic, mastery, onClick }) {
  return (
    <div className="topic-card" onClick={onClick} role="button" tabIndex={0}>
      <h3>{topic.title}</h3>
      <p>{topic.description}</p>
      <div className="topic-card-footer">
        <MasteryBadge status={mastery?.status} />
        <span className="text-muted" style={{ fontSize: "0.78rem" }}>
          p.{topic.page_range?.[0]}–{topic.page_range?.[1]}
        </span>
      </div>
    </div>
  );
}
