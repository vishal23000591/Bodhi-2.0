import { useEffect, useRef } from "react";

export default function ChatBubble({ message, autoRead, language }) {
  const isUser = message.role === "user";
  const hasRead = useRef(false);

  // Auto-Read on mount for new assistant messages
  useEffect(() => {
    // Only auto-read once on initial mount if autoRead is true and it's an assistant message
    if (autoRead && !isUser && message.content && !hasRead.current) {
      hasRead.current = true;
      
      const speech = new SpeechSynthesisUtterance(message.content);
      // Map app languages to browser BCP-47 tags
      if (language === 'ta') speech.lang = 'ta-IN';
      else if (language === 'tanglish') speech.lang = 'en-IN';
      else speech.lang = 'en-IN'; // Default to Indian English

      window.speechSynthesis.speak(speech);
    }
  }, []); // Run only once when the bubble mounts

  // Manual trigger for the speaker icon
  const handleManualSpeak = () => {
    window.speechSynthesis.cancel(); // Stop any currently playing audio
    const speech = new SpeechSynthesisUtterance(message.content);
    if (language === 'ta') speech.lang = 'ta-IN';
    else speech.lang = 'en-IN';
    window.speechSynthesis.speak(speech);
  };

  return (
    <div className={`chat-row ${isUser ? "user" : "assistant"}`}>
      {!isUser && <div className="chat-avatar">🌱</div>}
      <div>
        <div className={`bubble ${isUser ? "user" : "assistant"}`}>
          {message.content}
          
          {/* Small Speaker Icon for Manual TTS */}
          {!isUser && (
            <button 
              onClick={handleManualSpeak} 
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', marginLeft: '8px', fontSize: '1.1rem', padding: '0' }}
              title="Read Aloud"
              aria-label="Read text aloud"
            >
              🔊
            </button>
          )}
        </div>
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
