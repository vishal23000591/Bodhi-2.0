import { useEffect, useRef } from "react";
import { useAuth } from "../context/AuthContext";
import { DocumentIcon, LeafIcon, SpeakerIcon } from "./icons";

const VISIBLE_SOURCES = 4;

function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export default function ChatBubble({ message, autoRead, language }) {
  const isUser = message.role === "user";
  const hasRead = useRef(false);
  const { user } = useAuth();

  // Auto-Read on mount for new assistant messages
  useEffect(() => {
    // Only auto-read once on initial mount if autoRead is true and it's an assistant message
    if (autoRead && !isUser && message.content && !hasRead.current) {
      hasRead.current = true;

      const speech = new SpeechSynthesisUtterance(message.content);
      // Map app languages to browser BCP-47 tags
      if (language === "ta") speech.lang = "ta-IN";
      else if (language === "tanglish") speech.lang = "en-IN";
      else speech.lang = "en-IN"; // Default to Indian English

      window.speechSynthesis.speak(speech);
    }
  }, []); // Run only once when the bubble mounts

  // Manual trigger for the speaker icon
  const handleManualSpeak = () => {
    window.speechSynthesis.cancel(); // Stop any currently playing audio
    const speech = new SpeechSynthesisUtterance(message.content);
    if (language === "ta") speech.lang = "ta-IN";
    else speech.lang = "en-IN";
    window.speechSynthesis.speak(speech);
  };

  const time = formatTime(message.created_at);
  const sources = message.sources || [];
  const visibleSources = sources.slice(0, VISIBLE_SOURCES);
  const overflowCount = sources.length - visibleSources.length;
  const userInitial = (user?.name || "?").slice(0, 1).toUpperCase();

  return (
    <div className={`chat-msg-card ${isUser ? "user" : "assistant"}`}>
      <div className="chat-msg-header">
        <div className="chat-msg-header-left">
          {!isUser && (
            <>
              <div className="chat-avatar">
                <LeafIcon />
              </div>
              <span className="chat-sender-name">Bodhi</span>
            </>
          )}
          {isUser && time && <span className="chat-msg-time">{time}</span>}
        </div>
        <div className="chat-msg-header-right">
          {!isUser && time && <span className="chat-msg-time">{time}</span>}
          {!isUser && (
            <button
              onClick={handleManualSpeak}
              className="speak-btn"
              title="Read Aloud"
              aria-label="Read text aloud"
            >
              <SpeakerIcon />
            </button>
          )}
          {isUser && <div className="chat-avatar user">{userInitial}</div>}
        </div>
      </div>

      <div className="chat-msg-body">{message.content}</div>

      {!isUser && sources.length > 0 && (
        <>
          <div className="chat-msg-sources-label">Sources</div>
          <div className="source-chip-row">
            {visibleSources.map((s, i) => (
              <span key={i} className="source-chip">
                <DocumentIcon /> Textbook p.{s.page}
              </span>
            ))}
            {overflowCount > 0 && <span className="source-chip more">+{overflowCount} more</span>}
          </div>
        </>
      )}
    </div>
  );
}
