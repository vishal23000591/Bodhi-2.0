export default function ChatBubble({ message }) {
  const isUser = message.role === "user";
  return (
    <div className={`chat-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && <div className="chat-avatar">🌱</div>}
      <div>
        <div className={`bubble ${isUser ? "user" : "assistant"}`}>{message.content}</div>
        {!isUser && message.sources?.length > 0 && (
          <div className="source-chip-row">
            {message.sources.map((s, i) => (
              <span key={i} className="source-chip">
                📖 p.{s.page}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
