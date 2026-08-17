import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import ChatBubble from "../components/ChatBubble";
import LanguageToggle from "../components/LanguageToggle";
import LearnFlow from "../components/LearnFlow";
import MasteryBadge from "../components/MasteryBadge";
import { useLanguage } from "../hooks/useLanguage";

export default function Chat() {
  const { documentId, topicId } = useParams();
  const [topic, setTopic] = useState(null);
  const [view, setView] = useState("learn");
  const [chat, setChat] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [mastery, setMastery] = useState(null);
  const [language, setLanguage] = useLanguage();

  // The teach explanation is fetched once per topic here and shared by both
  // the Learn tab and the Ask-a-doubt concept-summary card — each tab used
  // to fetch it independently, and since LearnFlow was unmounted whenever
  // you switched away, every tab toggle silently re-spent a real LLM call.
  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [explanationError, setExplanationError] = useState("");

  const scrollRef = useRef(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setTopic(null);
      const topics = await api.topics(documentId);
      const found = topics.find((t) => t.id === topicId);
      if (cancelled) return;
      setTopic(found || null);

      const chatObj = await api.openChat({
        document_id: documentId,
        topic_id: topicId,
        title: found?.title || "Chat",
      });
      if (cancelled) return;
      setChat(chatObj);
      setMessages(await api.chatMessages(chatObj.id));
      refreshMastery();
    }

    load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId, topicId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const refreshMastery = useCallback(async () => {
    try {
      setMastery(await api.mastery(topicId));
    } catch {
      // non-critical
    }
  }, [topicId]);

  const loadExplanation = useCallback(async () => {
    setExplanationLoading(true);
    setExplanationError("");
    try {
      setExplanation(await api.teach(topicId, language));
    } catch (err) {
      setExplanationError(err.message);
    } finally {
      setExplanationLoading(false);
    }
  }, [topicId, language]);

  useEffect(() => {
    setExplanation(null);
    setExplanationError("");
    loadExplanation();
  }, [loadExplanation]);

  // --- VOICE MODE STATES & LOGIC ---
  const [isListening, setIsListening] = useState(false);
  const [autoRead, setAutoRead] = useState(false);

  const toggleListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert("Speech recognition is not supported in this browser.");
      return;
    }

    if (isListening) return; // Prevent multiple instances

    const recognition = new SpeechRecognition();
    
    // Dynamically set regional language
    if (language === 'ta') recognition.lang = 'ta-IN';
    else if (language === 'tanglish') recognition.lang = 'en-IN';
    else recognition.lang = 'en-IN';

    recognition.interimResults = true;
    recognition.continuous = false;

    const initialInput = input; // Capture current input to append safely

    recognition.onstart = () => setIsListening(true);

    recognition.onresult = (event) => {
      let currentTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        currentTranscript += event.results[i][0].transcript;
      }
      setInput(initialInput + (initialInput ? ' ' : '') + currentTranscript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };
  // ----------------------------------

  async function handleSend(e) {
    e.preventDefault();
    if (!input.trim() || !chat) return;
    const question = input.trim();
    setInput("");
    setSending(true);
    try {
      await api.ask(chat.id, question, language);
      setMessages(await api.chatMessages(chat.id));
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { id: `err-${Date.now()}`, role: "assistant", content: `Sorry, something went wrong: ${err.message}`, sources: [] },
      ]);
    } finally {
      setSending(false);
    }
  }

  if (!topic) {
    return (
      <div className="main-body">
        <p className="text-muted">Loading topic…</p>
      </div>
    );
  }

  return (
    <>
      <div className="main-header">
        <h1>{topic.title}</h1>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          {mastery && <MasteryBadge status={mastery.status} />}
          
          {/* New Auto-Read Toggle */}
          <label style={{ display: "flex", alignItems: "center", gap: "5px", fontSize: "0.9rem", cursor: "pointer", userSelect: "none" }}>
            <input 
              type="checkbox" 
              checked={autoRead} 
              onChange={(e) => setAutoRead(e.target.checked)} 
            />
            Auto-Read 🔊
          </label>

          <LanguageToggle language={language} onChange={setLanguage} />
          <button className={`btn ${view === "learn" ? "btn-primary" : "btn-secondary"}`} onClick={() => setView("learn")}>
            Learn
          </button>
          <button className={`btn ${view === "ask" ? "btn-primary" : "btn-secondary"}`} onClick={() => setView("ask")}>
            Ask a doubt
          </button>
        </div>
      </div>
      <div className="main-body">
        {/* Both tabs stay mounted (toggled via CSS, not conditional render)
            so switching between them never discards in-progress practice
            state or re-fetches the explanation. */}
        <div style={{ display: view === "learn" ? "block" : "none" }}>
          <LearnFlow
            key={topicId}
            topic={topic}
            language={language}
            explanation={explanation}
            explanationLoading={explanationLoading}
            explanationError={explanationError}
            onReloadExplanation={loadExplanation}
            onMasteryChange={refreshMastery}
          />
        </div>
        <div style={{ display: view === "ask" ? "block" : "none" }}>
          <div className="chat-scroll">
            {explanationLoading && !explanation && (
              <div className="upload-status" style={{ marginBottom: 4 }}>
                <div className="spinner" /> Preparing a summary of this concept…
              </div>
            )}
            {explanation && (
              <div className="card concept-summary">
                <h4>📖 Concept Summary — {topic.title}</h4>
                <p>{explanation.explanation}</p>
                {explanation.sources?.length > 0 && (
                  <div className="source-chip-row">
                    {explanation.sources.map((s, i) => (
                      <span key={i} className="source-chip">
                        📖 p.{s.page}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
            {messages.length === 0 && (
              <div className="empty-state">Ask anything about {topic.title} — Bodhi will answer using your textbook.</div>
            )}
            {messages.map((m) => (
              <ChatBubble 
                key={m.id} 
                message={m} 
                autoRead={autoRead} 
                language={language} 
              />
            ))}
            <div ref={scrollRef} />
          </div>
          <form className="chat-composer" onSubmit={handleSend}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your doubt or use voice…"
              disabled={sending}
            />
            
            {/* New Microphone Button */}
            <button 
              type="button" 
              className="btn btn-secondary" 
              onClick={toggleListening}
              title="Voice Input"
              style={{
                padding: '0 14px',
                color: isListening ? '#ef4444' : 'inherit',
                backgroundColor: isListening ? '#fee2e2' : undefined,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s',
              }}
            >
              {isListening ? '🎙️...' : '🎤'}
            </button>

            <button className="btn btn-primary" type="submit" disabled={sending || !input.trim()}>
              {sending ? "…" : "Send"}
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
