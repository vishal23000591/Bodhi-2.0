import { useState } from "react";
import { api } from "../api/client";

const STAGE = {
  TEACHING: "teaching",
  TEACHBACK_QUESTION: "teachback_question",
  DIAGNOSIS: "diagnosis",
  PRACTICE: "practice",
  PRACTICE_RESULT: "practice_result",
};

/** The full "teach -> teach-back -> diagnose -> practice -> mastery" loop
 * from the architecture doc (section 6), scoped to a single topic.
 *
 * The teach explanation itself is fetched once by the parent (Chat.jsx) and
 * shared with the "Ask a doubt" tab's concept-summary card, rather than
 * fetched here — this component used to re-fetch it on every mount, and
 * since it was conditionally rendered, every tab switch silently burned a
 * real LLM call against the OpenRouter daily quota. */
export default function LearnFlow({
  topic,
  language,
  explanation,
  explanationLoading,
  explanationError,
  onReloadExplanation,
  onMasteryChange,
}) {
  const [stage, setStage] = useState(STAGE.TEACHING);
  const [tbQuestion, setTbQuestion] = useState("");
  const [tbAnswer, setTbAnswer] = useState("");
  const [diagnosis, setDiagnosis] = useState(null);
  const [practiceSet, setPracticeSet] = useState(null);
  const [qIndex, setQIndex] = useState(0);
  const [mcqAnswers, setMcqAnswers] = useState([]);
  const [shortAnswers, setShortAnswers] = useState([]);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function backToTeaching() {
    setStage(STAGE.TEACHING);
    setError("");
    onReloadExplanation();
  }

  async function handleUnderstood() {
    setBusy(true);
    setError("");
    try {
      const data = await api.teachbackQuestion(topic.id, language);
      setTbQuestion(data.question);
      setTbAnswer("");
      setStage(STAGE.TEACHBACK_QUESTION);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleCheckUnderstanding() {
    if (!tbAnswer.trim()) return;
    setBusy(true);
    setError("");
    try {
      const data = await api.teachbackAnswer(topic.id, tbAnswer.trim(), language);
      setDiagnosis(data);
      setStage(STAGE.DIAGNOSIS);
      onMasteryChange?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleStartPractice() {
    setBusy(true);
    setError("");
    try {
      const data = await api.generatePractice(topic.id, language);
      setPracticeSet(data);
      setMcqAnswers(new Array(data.mcqs.length).fill(null));
      setShortAnswers(new Array(data.short_answers.length).fill(""));
      setQIndex(0);
      setStage(STAGE.PRACTICE);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleSubmitPractice() {
    setBusy(true);
    setError("");
    try {
      const data = await api.submitPractice(practiceSet.id, {
        mcq_answers: mcqAnswers.map((a) => (a === null ? -1 : a)),
        short_answers: shortAnswers,
      });
      setResult(data);
      setStage(STAGE.PRACTICE_RESULT);
      onMasteryChange?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <div className="center-col">
        <div className="form-error">{error}</div>
        <button className="btn btn-secondary" onClick={() => setError("")}>
          Try again
        </button>
      </div>
    );
  }

  if (stage === STAGE.TEACHING) {
    if (explanationLoading && !explanation) {
      return (
        <div className="center-col">
          <div className="upload-status">
            <div className="spinner" /> Preparing this topic…
          </div>
        </div>
      );
    }

    if (explanationError) {
      return (
        <div className="center-col">
          <div className="form-error">{explanationError}</div>
          <button className="btn btn-secondary" onClick={onReloadExplanation}>
            Try again
          </button>
        </div>
      );
    }

    if (!explanation) return null;

    return (
      <div className="center-col">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>{topic.title}</h2>
          <p style={{ lineHeight: 1.6 }}>{explanation.explanation}</p>
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
        <div className="action-row">
          <button className="btn btn-primary" disabled={busy} onClick={handleUnderstood}>
            {busy ? "One sec…" : "I Understood"}
          </button>
        </div>
      </div>
    );
  }

  if (stage === STAGE.TEACHBACK_QUESTION) {
    return (
      <div className="center-col">
        <div className="card">
          <h2 style={{ marginTop: 0 }}>🧠 Your Turn</h2>
          <p>{tbQuestion}</p>
          <p className="text-muted" style={{ fontSize: "0.82rem" }}>
            Don't worry about using textbook language.
          </p>
          <textarea
            className="teachback-answer"
            value={tbAnswer}
            onChange={(e) => setTbAnswer(e.target.value)}
            placeholder="Type your answer in your own words…"
          />
          <div className="action-row" style={{ marginTop: 0 }}>
            <button
              className="btn btn-primary"
              disabled={busy || !tbAnswer.trim()}
              onClick={handleCheckUnderstanding}
            >
              {busy ? "Checking…" : "Check My Understanding"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (stage === STAGE.DIAGNOSIS) {
    return (
      <div className="center-col">
        <div className="card">
          <h2 style={{ marginTop: 0, textAlign: "center" }}>Your Understanding</h2>
          <div className="score-ring">{diagnosis.score}%</div>
          {diagnosis.understood?.length > 0 && (
            <div className="diagnosis-section understood">
              <h4>✓ You understood</h4>
              <ul>
                {diagnosis.understood.map((u, i) => (
                  <li key={i}>{u}</li>
                ))}
              </ul>
            </div>
          )}
          {diagnosis.partial?.length > 0 && (
            <div className="diagnosis-section">
              <h4>△ Partial</h4>
              <ul>
                {diagnosis.partial.map((p, i) => (
                  <li key={i}>{p}</li>
                ))}
              </ul>
            </div>
          )}
          {diagnosis.misconceptions?.length > 0 && (
            <div className="diagnosis-section misconception">
              <h4>⚠ Misconception</h4>
              {diagnosis.misconceptions.map((m, i) => (
                <div className="misconception-box" key={i}>
                  You said {m.claim}. According to your textbook: {m.correction}
                </div>
              ))}
            </div>
          )}
        </div>
        <div className="action-row">
          <button className="btn btn-secondary" disabled={busy} onClick={backToTeaching}>
            Learn This Again
          </button>
          <button className="btn btn-primary" disabled={busy} onClick={handleStartPractice}>
            {busy ? "Preparing…" : "Start Practice →"}
          </button>
        </div>
      </div>
    );
  }

  if (stage === STAGE.PRACTICE) {
    const totalMcq = practiceSet.mcqs.length;
    const total = totalMcq + practiceSet.short_answers.length;
    const isMcq = qIndex < totalMcq;
    const isLast = qIndex === total - 1;

    function selectMcq(optionIndex) {
      const next = [...mcqAnswers];
      next[qIndex] = optionIndex;
      setMcqAnswers(next);
    }

    function setShortAnswer(value) {
      const next = [...shortAnswers];
      next[qIndex - totalMcq] = value;
      setShortAnswers(next);
    }

    const canAdvance = isMcq
      ? mcqAnswers[qIndex] !== null
      : shortAnswers[qIndex - totalMcq]?.trim().length > 0;

    return (
      <div className="center-col">
        <div className="practice-progress">
          Practice · {topic.title} · Question {qIndex + 1} of {total}
        </div>
        <div className="card">
          {isMcq ? (
            <>
              <h3 style={{ marginTop: 0 }}>{practiceSet.mcqs[qIndex].question}</h3>
              {practiceSet.mcqs[qIndex].options.map((opt, i) => (
                <div
                  key={i}
                  className={`mcq-option ${mcqAnswers[qIndex] === i ? "selected" : ""}`}
                  onClick={() => selectMcq(i)}
                >
                  <span>{String.fromCharCode(65 + i)}.</span> {opt}
                </div>
              ))}
            </>
          ) : (
            <>
              <h3 style={{ marginTop: 0 }}>{practiceSet.short_answers[qIndex - totalMcq].question}</h3>
              <textarea
                className="teachback-answer"
                value={shortAnswers[qIndex - totalMcq]}
                onChange={(e) => setShortAnswer(e.target.value)}
                placeholder="Your answer…"
              />
            </>
          )}
        </div>
        <div className="action-row">
          {qIndex > 0 && (
            <button className="btn btn-secondary" onClick={() => setQIndex(qIndex - 1)}>
              ← Back
            </button>
          )}
          {!isLast && (
            <button className="btn btn-primary" disabled={!canAdvance} onClick={() => setQIndex(qIndex + 1)}>
              Next Question →
            </button>
          )}
          {isLast && (
            <button className="btn btn-primary" disabled={!canAdvance || busy} onClick={handleSubmitPractice}>
              {busy ? "Scoring…" : "Submit Practice"}
            </button>
          )}
        </div>
      </div>
    );
  }

  if (stage === STAGE.PRACTICE_RESULT) {
    const totalMcq = practiceSet.mcqs.length;
    return (
      <div className="center-col">
        <div className="card">
          <h2 style={{ marginTop: 0, textAlign: "center" }}>Practice Results</h2>
          <div className="score-ring">{result.overall_score}%</div>
          <p style={{ textAlign: "center" }} className="text-muted">
            MCQs: {result.mcq_score}
          </p>

          {practiceSet.mcqs.map((mcq, i) => {
            const given = mcqAnswers[i];
            const correctIndex = result.mcq_correct_indices[i];
            const isCorrect = given === correctIndex;
            return (
              <div key={i} style={{ marginBottom: 14 }}>
                <p style={{ marginBottom: 6, fontWeight: 600 }}>
                  {i + 1}. {mcq.question}
                </p>
                {mcq.options.map((opt, oi) => {
                  let cls = "mcq-option";
                  if (oi === correctIndex) cls += " correct";
                  else if (oi === given) cls += " incorrect";
                  return (
                    <div key={oi} className={cls}>
                      {String.fromCharCode(65 + oi)}. {opt}
                    </div>
                  );
                })}
                {!isCorrect && (
                  <div className="feedback-note incorrect">
                    Not quite — the correct answer is "{mcq.options[correctIndex]}".
                  </div>
                )}
              </div>
            );
          })}

          {practiceSet.short_answers.map((sa, i) => (
            <div key={i} style={{ marginBottom: 14 }}>
              <p style={{ marginBottom: 6, fontWeight: 600 }}>
                {totalMcq + i + 1}. {sa.question}
              </p>
              <p className="text-muted" style={{ fontSize: "0.85rem" }}>
                Your answer: {shortAnswers[i]}
              </p>
              <div className={`feedback-note ${result.short_answer_scores[i] >= 70 ? "correct" : "incorrect"}`}>
                {result.short_answer_scores[i]}% — {result.short_answer_explanations[i]}
              </div>
            </div>
          ))}
        </div>
        <div className="action-row">
          <button className="btn btn-secondary" onClick={backToTeaching}>
            Learn This Again
          </button>
          <button className="btn btn-primary" onClick={handleStartPractice}>
            Practice Again
          </button>
        </div>
      </div>
    );
  }

  return null;
}
