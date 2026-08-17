# BODHI — Technical Architecture
### Your book. Your language. Your understanding.

> A textbook-grounded AI tutor. The student uploads a textbook (PDF), Bodhi turns it into topics, and the student picks a topic and asks doubts — answered only from that textbook, in a chat interface that feels like a study app for school students, not a generic AI tool.

This document locks the **tech stack** and **system design** for the build:

| Layer | Choice |
|---|---|
| PDF text check + extraction | **PyMuPDF (fitz)** — used when the PDF has a real text layer |
| Scanned / image PDF extraction | **PaddleOCR** — used when the PDF is copy-paste-proof (no text layer) |
| LLM (topics + answers) | **OpenRouter** (chat completions API) |
| Embeddings | **OpenRouter embedding model** |
| Vector store | **ChromaDB** |
| Auth + app data (users, chats) | **MongoDB** |
| Backend | **FastAPI** (Python — same runtime as the extraction/OCR/LLM pipeline) |
| Frontend | **React**, peach/warm design system, ChatGPT/Claude-style left sidebar |

---

## 1. Product Shape

Bodhi is **not** a general chatbot. Every answer must come from the uploaded textbook.

```
Upload PDF
   ↓
Detect PDF type (copy-paste vs scanned)
   ↓
Extract text (PyMuPDF or PaddleOCR)
   ↓
Send text → OpenRouter LLM → generate concept/topic list
   ↓
Chunk text → OpenRouter embeddings → store in ChromaDB
   ↓
Student picks a topic from the generated list
   ↓
Bodhi teaches the topic (grounded explanation)
   ↓
Student clicks "I Understood"
   ↓
Bodhi asks a teach-back question on that topic
   ↓
Student answers in their own words
   ↓
Diagnosis Agent scores the answer (% understanding + misconceptions)
   ↓
Bodhi generates 5 MCQs + 2 short-answer questions on the topic
   ↓
Student attempts practice → each answer scored, wrong ones explained
   ↓
Topic mastery % updated → student can revisit or move to next topic
   │
   ▼ (in parallel, any time)
Student asks a free-form doubt
   ↓
Retrieve relevant chunks from ChromaDB (scoped to that document + topic)
   ↓
OpenRouter LLM answers using ONLY retrieved chunks
   ↓
Answer + sources saved to that chat session (MongoDB)
```

---

## 2. High-Level System Diagram

```
┌───────────────────────────────────────────────────────────────────┐
│                            FRONTEND (React)                       │
│                                                                     │
│  ┌───────────────┐   ┌───────────────────────────────────────┐   │
│  │  Left Sidebar  │   │              Main Panel                │   │
│  │  ─────────────│   │  ───────────────────────────────────── │   │
│  │  + New Chat    │   │  Upload screen / Topic picker /        │   │
│  │  🔍 Search     │   │  Chat window (doubt Q&A on a topic)    │   │
│  │  ─────────────│   │                                         │   │
│  │  📄 Chapter 4  │   │                                         │   │
│  │    Today       │   │                                         │   │
│  │  📄 Photosynth │   │                                         │   │
│  │    Yesterday   │   │                                         │   │
│  │  ─────────────│   │                                         │   │
│  │  👤 Profile    │   │                                         │   │
│  └───────────────┘   └───────────────────────────────────────┘   │
└──────────────────────────────┬──────────────────────────────────┘
                                │ REST / JWT
                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                          │
│                                                                     │
│  auth/            documents/         topics/          chat/       │
│  ─────            ─────────          ──────           ────        │
│  signup, login    upload, type       generate          ask,       │
│  JWT issue        detect, extract    topics via         history   │
│                    (PyMuPDF/         OpenRouter                    │
│                     PaddleOCR)                                     │
│                                                                     │
│  rag/                                services/                     │
│  ────                                ────────                      │
│  chunk, embed (OpenRouter),          openrouter_client.py          │
│  store/query ChromaDB                mongo_client.py               │
│                                       chroma_client.py              │
└───────┬───────────────────┬──────────────────────┬────────────────┘
        │                   │                       │
        ▼                   ▼                       ▼
 ┌─────────────┐   ┌────────────────┐      ┌──────────────────┐
 │  MongoDB    │   │   ChromaDB      │      │   OpenRouter API  │
 │  users      │   │  (persistent)   │      │  (LLM + embed)    │
 │  documents  │   │  one collection │      │                    │
 │  topics     │   │  per document,  │      └──────────────────┘
 │  chats      │   │  chunk vectors  │
 │  messages   │   └────────────────┘
 └─────────────┘
```

---

## 3. Ingestion Pipeline — Copy-Paste Detection → Extraction

This is the core routing decision the user described: **check if the PDF text is selectable ("copy-paste") before choosing an extractor.**

```
POST /documents/upload  (PDF file)
        │
        ▼
open with PyMuPDF (fitz.open)
        │
        ▼
for each page: page.get_text("text")
        │
        ▼
total extractable characters ≥ threshold (e.g. > 30 chars/page average)?
        │
   ┌────┴────┐
   │ YES     │ NO
   ▼         ▼
COPY-PASTE   SCANNED / IMAGE PDF
PDF          │
   │         ▼
   │     Render each page to image (PyMuPDF: page.get_pixmap)
   │         │
   │         ▼
   │     Run PaddleOCR on each page image
   │         │
   │         ▼
   │     Reconstruct page-wise text (with OCR confidence)
   │         │
   └────┬────┘
        ▼
  EXTRACTED_TEXT (per page, with page numbers preserved)
```

**Why PyMuPDF is checked first on every upload:** it's fast (no ML inference) and works even for OCR-routed PDFs, since it is also used to rasterize pages for PaddleOCR. So `document_service.py` always opens with PyMuPDF; PaddleOCR is only invoked conditionally.

```python
# services/document_service.py (shape, not full code)
def extract_text(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages = []
    is_copy_paste = True

    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if len(text) < MIN_CHARS_PER_PAGE:
            is_copy_paste = False
        pages.append({"page_number": i + 1, "text": text})

    if is_copy_paste:
        return pages  # PyMuPDF output is final

    # fallback: OCR every page
    ocr_pages = []
    for i, page in enumerate(doc):
        pix = page.get_pixmap(dpi=200)
        img_path = f"/tmp/{doc_id}_page_{i+1}.png"
        pix.save(img_path)
        ocr_result = paddle_ocr.ocr(img_path)
        ocr_pages.append({
            "page_number": i + 1,
            "text": " ".join(line[1][0] for line in ocr_result[0])
        })
    return ocr_pages
```

Output is stored as `document_chunks` in MongoDB, keyed by `document_id` + `page_number`, before chunking for embeddings.

---

## 4. Topic / Concept Generation — OpenRouter LLM

Once extraction finishes, the full extracted text (or a page-batched map-reduce if the book is long) is sent to an OpenRouter chat model to produce a structured topic list — this is what the student picks from.

```
POST /documents/{id}/topics/generate
        │
        ▼
Build prompt:
  "Here is textbook content. Extract 8–15 distinct teachable
   concepts/topics, in the order they appear. For each, give a
   short title, the page range it's grounded in, and a one-line
   description. Return strict JSON."
        │
        ▼
OpenRouter chat.completions (model: e.g. anthropic/claude-*,
openai/gpt-4o-mini, or any configured OpenRouter model)
        │
        ▼
Parse JSON → store in `topics` collection (MongoDB)
        │
        ▼
Frontend renders topic cards for the student to pick from
```

Example OpenRouter call:

```python
# services/openrouter_client.py
async def generate_topics(text: str) -> list[dict]:
    response = await client.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"},
        json={
            "model": OPENROUTER_CHAT_MODEL,
            "messages": [
                {"role": "system", "content": TOPIC_EXTRACTION_PROMPT},
                {"role": "user", "content": text},
            ],
            "response_format": {"type": "json_object"},
        },
    )
    return json.loads(response.json()["choices"][0]["message"]["content"])["topics"]
```

---

## 5. Embedding + ChromaDB (RAG for Doubts)

Extracted text is chunked and embedded so that when the student asks a doubt, Bodhi retrieves only the relevant grounded passages — never answering from general knowledge.

```
EXTRACTED_TEXT (per page)
       │
       ▼
Chunk (e.g. ~500–800 tokens, with page number + topic tag kept as metadata)
       │
       ▼
OpenRouter embeddings endpoint → vector per chunk
       │
       ▼
ChromaDB.add(
    ids=[chunk_id],
    embeddings=[vector],
    documents=[chunk_text],
    metadatas=[{document_id, topic_id, page_number}]
)
       │
       ▼
One Chroma collection per document (collection_name = document_id)
```

**Ask a doubt flow:**

```
POST /chat/{chat_id}/ask   { "message": "why does..." }
        │
        ▼
Embed the student's question (OpenRouter embeddings)
        │
        ▼
ChromaDB.query(collection=document_id, query_embedding, 
                where={"topic_id": current_topic_id}, n_results=5)
        │
        ▼
Build grounded prompt:
  SYSTEM: "You are Bodhi. Answer ONLY using the provided textbook
  excerpts. If the question is out of scope, say so — do not guess."
  CONTEXT: <retrieved chunks with page numbers>
  QUESTION: <student question>
        │
        ▼
OpenRouter chat.completions → answer
        │
        ▼
Save {question, answer, sources[page_numbers]} to `messages` (MongoDB)
        │
        ▼
Stream/return answer to chat window
```

---

## 6. Teach-Back → Score → Practice (5 MCQs + 2 Short Answers)

This is the loop from the uploaded architecture doc that makes Bodhi more than a Q&A chatbot: after the student says **"I Understood"** on a topic, Bodhi checks that understanding before moving on.

```
Bodhi teaches the topic (grounded explanation, from RAG context)
        │
        ▼
Student clicks [ I Understood ]
        │
        ▼
POST /topics/{topic_id}/teachback/question
   → OpenRouter LLM generates ONE teach-back question
     ("Explain photosynthesis in your own words.")
        │
        ▼
Student types a free-text answer
        │
        ▼
POST /topics/{topic_id}/teachback/answer   { answer }
        │
        ▼
   ┌─────────────────────────────────────────────┐
   │            DIAGNOSIS / SCORING                │
   │                                               │
   │  1. LLM extracts claims from student answer   │
   │  2. Each claim compared against retrieved     │
   │     textbook evidence (ChromaDB, same topic)  │
   │  3. Claims classified:                        │
   │       ✓ Understood                            │
   │       △ Partial                               │
   │       ✗ Misconception                         │
   │  4. Score = weighted % of concept covered      │
   └─────────────────────────────────────────────┘
        │
        ▼
Response shown to student:
   { score: 62, understood: [...], partial: [...],
     misconceptions: [...] }
        │
        ▼
POST /topics/{topic_id}/practice/generate
   → OpenRouter LLM generates practice set for this topic:
        5 MCQs      (one option is a misconception-based
                      distractor if a misconception was found)
      + 2 Short Answers
        │
        ▼
Student attempts each question
        │
        ▼
POST /practice/{attempt_id}/submit   { answers }
        │
        ▼
   MCQs   → scored directly (exact match)
   Short  → same LLM-diagnosis approach as teach-back
        │
        ▼
Wrong answers → short explanation shown immediately
        │
        ▼
Topic mastery % recalculated → stored on student_concept_mastery
        │
        ▼
   mastery >= 80%  → topic marked "Mastered", suggest next topic
   50–79%          → stays "In Progress"
   < 50%           → suggest "Learn This Again" (reteach)
```

**Teach-back UI:**

```
┌──────────────────────────────────────────────────────────┐
│                    🧠 YOUR TURN                          │
│                                                          │
│ Explain photosynthesis in your own words.                │
│ Don't worry about using textbook language.               │
│                                                          │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ Plants use sunlight and oxygen to make food...        │ │
│ └──────────────────────────────────────────────────────┘ │
│                                                          │
│             [ Check My Understanding ]                  │
└──────────────────────────────────────────────────────────┘
```

**Score / diagnosis UI:**

```
┌──────────────────────────────────────────────────────────┐
│                  YOUR UNDERSTANDING                      │
│                                                          │
│                         62%                              │
│                                                          │
│ ✓ You understood                                         │
│   • Sunlight is involved                                 │
│   • Plants prepare food                                  │
│                                                          │
│ ⚠ Misconception                                          │
│   You said plants use oxygen to make food.               │
│   According to your textbook, oxygen is produced         │
│   during photosynthesis, not used as an input.            │
│                                                          │
│        [ Learn This Again ]   [ Start Practice → ]      │
└──────────────────────────────────────────────────────────┘
```

**Practice UI (5 MCQs + 2 short answers):**

```
┌──────────────────────────────────────────────────────────┐
│  Practice · Photosynthesis            Question 2 of 7    │
│                                                          │
│  Which substance is produced as food during              │
│  photosynthesis?                                         │
│                                                          │
│   ○ A. Glucose                                           │
│   ● B. Oxygen                                             │
│   ○ C. Water                                              │
│   ○ D. Carbon dioxide                                     │
│                                                          │
│  ❌ Not quite. Oxygen is produced during photosynthesis,  │
│     but glucose is the food the plant makes.              │
│                                                          │
│                                     [ Next Question → ]   │
└──────────────────────────────────────────────────────────┘
```

**Data model additions (MongoDB):**

```jsonc
// student_concept_mastery
{
  "user_id": "user_001",
  "topic_id": "topic_001",
  "mastery": 0.62,
  "status": "in_progress",   // mastered | in_progress | needs_reteach
  "last_updated": "..."
}

// teachback_attempts
{
  "_id": "tb_001",
  "user_id": "user_001",
  "topic_id": "topic_001",
  "question": "Explain photosynthesis in your own words.",
  "answer": "Plants use sunlight and oxygen to make food.",
  "score": 62,
  "understood": ["Sunlight is involved", "Plants prepare food"],
  "partial": ["Water", "Carbon dioxide"],
  "misconceptions": [{"claim": "oxygen is an input", "confidence": 0.87}],
  "created_at": "..."
}

// practice_sets
{
  "_id": "practice_001",
  "topic_id": "topic_001",
  "mcqs": [
    {
      "question": "Which substance is produced as food during photosynthesis?",
      "options": ["Glucose", "Oxygen", "Water", "Carbon dioxide"],
      "correct_index": 0,
      "distractor_note": "Oxygen chosen → known misconception: oxygen = food"
    }
    // ...5 total
  ],
  "short_answers": [
    { "question": "What happens to a plant kept without sunlight?" }
    // ...2 total
  ]
}

// practice_attempts
{
  "_id": "attempt_001",
  "user_id": "user_001",
  "practice_set_id": "practice_001",
  "mcq_answers": [0, 1, 2, 0, 3],
  "mcq_score": "4/5",
  "short_answers": ["...", "..."],
  "short_answer_scores": [80, 55],
  "overall_score": 71,
  "created_at": "..."
}
```

---

## 7. Auth — MongoDB + JWT

Simple signup/login, since this is a "teachable platform" students log into, not a research MVP.

**Collections:**

```jsonc
// users
{
  "_id": "ObjectId",
  "name": "Vishal",
  "email": "student@example.com",
  "password_hash": "bcrypt(...)",
  "grade": "10",              // optional, nice for a school-facing UI
  "preferred_language": "ta",
  "created_at": "..."
}
```

**Flow:**

```
POST /auth/signup  { name, email, password }
   → hash password (bcrypt) → insert into users → issue JWT

POST /auth/login   { email, password }
   → verify bcrypt hash → issue JWT (access + refresh)

All other routes → Authorization: Bearer <JWT>
   → FastAPI dependency decodes JWT → attaches user_id to request
```

---

## 8. Chat History (Sidebar) — MongoDB

This is the ChatGPT/Claude-style left sidebar the user asked for: one entry per uploaded document/topic session, grouped by recency, clickable to resume.

**Collections:**

```jsonc
// documents
{
  "_id": "doc_001",
  "user_id": "user_001",
  "filename": "Chapter 4 - Photosynthesis.pdf",
  "extraction_mode": "copy_paste" | "ocr",
  "status": "processing" | "ready" | "failed",
  "page_count": 24,
  "created_at": "..."
}

// topics
{
  "_id": "topic_001",
  "document_id": "doc_001",
  "title": "Photosynthesis",
  "description": "How plants convert light into energy",
  "page_range": [10, 14]
}

// chats            (one chat = one topic session, shown in sidebar)
{
  "_id": "chat_001",
  "user_id": "user_001",
  "document_id": "doc_001",
  "topic_id": "topic_001",
  "title": "Photosynthesis",       // sidebar label
  "last_message_at": "...",
  "created_at": "..."
}

// messages
{
  "_id": "msg_001",
  "chat_id": "chat_001",
  "role": "user" | "assistant",
  "content": "...",
  "sources": [{"page": 12}],       // only on assistant messages
  "created_at": "..."
}
```

**Sidebar API:**

```
GET  /chats                    → grouped list (Today / Yesterday / This week)
GET  /chats/{chat_id}/messages → full thread when a sidebar item is clicked
POST /chats                    → created automatically when a topic is first opened
DELETE /chats/{chat_id}        → remove from sidebar
```

---

## 9. Full Backend Folder Structure

```
backend/
├── app/
│   ├── main.py
│   ├── auth/
│   │   ├── routes.py            # signup, login
│   │   ├── jwt_handler.py
│   │   └── dependencies.py      # get_current_user
│   ├── documents/
│   │   ├── routes.py            # upload, status
│   │   └── document_service.py  # PyMuPDF check + PaddleOCR fallback
│   ├── topics/
│   │   └── routes.py            # generate + list topics
│   ├── chat/
│   │   ├── routes.py            # ask, history, list chats
│   │   └── chat_service.py
│   ├── rag/
│   │   ├── chunking.py
│   │   ├── embeddings.py        # OpenRouter embeddings
│   │   └── chroma_store.py
│   ├── services/
│   │   ├── openrouter_client.py
│   │   ├── mongo_client.py
│   │   └── ocr_service.py       # PaddleOCR wrapper
│   ├── models/                  # Pydantic schemas
│   └── prompts/
│       ├── topic_prompt.py
│       └── tutor_prompt.py
└── requirements.txt
```

```
frontend/
├── src/
│   ├── pages/
│   │   ├── Login.jsx / Signup.jsx
│   │   ├── Home.jsx              # upload screen
│   │   ├── Topics.jsx            # topic picker cards
│   │   └── Chat.jsx              # main Q&A window
│   ├── components/
│   │   ├── Sidebar.jsx           # chat history, ChatGPT/Claude style
│   │   ├── UploadBox.jsx
│   │   ├── TopicCard.jsx
│   │   ├── ChatBubble.jsx
│   │   └── SourceBadge.jsx       # shows "p.12" under grounded answers
│   ├── styles/
│   │   └── theme.css             # peach design tokens (below)
│   └── App.jsx
```

---

## 10. UI / Design System — "Not AI, More School"

The brief: use the logo's **elegant peach/cream** background, and make the product feel like a friendly study app, not a technical AI console (no dark mode, no terminal-green, no cold blues).

**Color tokens** (sampled from the Bodhi logo — sun, soil, and leaf):

```css
:root {
  /* base */
  --bg-page:        #F1E7D8;   /* elegant peach/cream — main background */
  --bg-surface:     #FBF6EE;   /* card / panel background, slightly lighter */
  --bg-sidebar:     #EBDCC6;   /* soft warm tan, sits behind main panel */

  /* accents, from the logo */
  --accent-sun:     #E0A94B;   /* warm gold — primary buttons, highlights */
  --accent-terracotta: #B5502E; /* rust/clay — active states, badges */
  --accent-leaf:    #6E8B5C;   /* sage green — success, "mastered" states */

  /* text */
  --text-primary:   #3B2E22;   /* deep bronze-brown, not pure black */
  --text-secondary: #7A6952;

  /* borders / lines */
  --border-soft:    #DCC9AC;
}
```

**Layout principles:**

- **Left sidebar** (peach-tan `--bg-sidebar`): "+ New chat" button in warm gold, search box, chat history list grouped by *Today / Yesterday / This week*, each item = document/topic title with a small book icon. Active chat highlighted with a soft terracotta left-border, not a harsh blue.
- **Main panel** (`--bg-surface` cards on `--bg-page`): rounded corners (16–20px), soft drop shadows, generous padding — feels like a notebook/workbook, not a dashboard.
- **Typography:** a rounded, friendly sans-serif (e.g. Nunito, Poppins, or Quicksand) instead of a technical mono/grotesk — this alone is what makes it read as "for students," not "for developers."
- **Chat bubbles:** student messages in a soft terracotta-tinted bubble; Bodhi's answers in a cream card with a small leaf icon avatar (matching the logo's leaf) instead of a robot/AI icon. Grounded answers show a small "📖 p.12" source chip instead of a plain citation link.
- **Empty/upload state:** large, illustrated upload box with soft rounded corners, gold dashed border, "📚 Drop your textbook here" — playful, not a bare file-input.
- **No neon, no glassmorphism, no dark theme by default** — this is a deliberate anti-"AI product" choice per the brief.

**Wireframe — main shell:**

```
┌───────────────┬─────────────────────────────────────────────┐
│  🌱 BODHI      │   Photosynthesis                    👤 Vishal │
│               │  ──────────────────────────────────────────  │
│  + New chat   │                                               │
│  🔍 Search    │   [Bodhi]  Photosynthesis is how plants...   │
│  ──────────   │            📖 p.12                            │
│  Today        │                                               │
│   📄 Photo..  │              [You]  why do plants need water? │
│  Yesterday    │                                               │
│   📄 Chap 3   │   [Bodhi]  Great question! According to...   │
│               │            📖 p.13                            │
│               │  ──────────────────────────────────────────  │
│               │   [ Type your doubt...              ] [Send] │
└───────────────┴─────────────────────────────────────────────┘
```

---

## 11. End-to-End API Summary

```
POST   /auth/signup
POST   /auth/login

POST   /documents/upload              → { document_id, status: "processing" }
GET    /documents/{id}/status         → { status, page_count, extraction_mode }
POST   /documents/{id}/topics/generate
GET    /documents/{id}/topics         → [ {title, description, page_range} ]

POST   /topics/{id}/teach                     → grounded explanation for the topic
POST   /topics/{id}/teachback/question        → generates the "explain in your own words" question
POST   /topics/{id}/teachback/answer          → { answer } → { score, understood, partial, misconceptions }
POST   /topics/{id}/practice/generate         → { mcqs: [...5], short_answers: [...2] }
POST   /practice/{attempt_id}/submit          → { mcq_answers, short_answers } → scored + explanations
GET    /topics/{id}/mastery                   → current mastery % + status for this student

POST   /chats                         → create/open a chat for a topic
GET    /chats                         → sidebar list, grouped by recency
GET    /chats/{chat_id}/messages
POST   /chats/{chat_id}/ask           → { message } → grounded answer + sources
DELETE /chats/{chat_id}
```

---

## 12. Build Priority (MVP Lock)

```
MANDATORY (P0)
──────────────────────────────
✓ Signup / login (MongoDB + JWT)
✓ PDF upload + copy-paste vs scanned detection
✓ PyMuPDF extraction
✓ PaddleOCR fallback extraction
✓ Topic generation via OpenRouter
✓ Chunk + embed (OpenRouter) → ChromaDB
✓ Topic picker UI
✓ Doubt-asking chat grounded in ChromaDB retrieval
✓ "I Understood" → teach-back question → scored diagnosis
✓ 5 MCQs + 2 short-answer practice generation & scoring
✓ Topic mastery % (mastered / in progress / needs reteach)
✓ Chat history sidebar (MongoDB)
✓ Peach/student-friendly UI shell

DIFFERENTIATION (P1)
──────────────────────────────
○ Out-of-scope guardrail ("that's not in this chapter")
○ Multi-language answers (student's mother tongue)
○ Source page chips on every answer
○ Misconception-based MCQ distractors
○ Adaptive difficulty (raise/lower next question based on score)
○ Rename / delete chats in sidebar

STRETCH (P2)
──────────────────────────────
○ Adaptive reteaching with a different strategy (analogy → example)
○ Transfer / application questions beyond the 7-question set
○ Mastery dashboard across all topics in a document
○ Revision scheduling for weak topics
```

The P0 list is a complete, demoable product: sign up → upload a textbook → see topics → pick one → get taught → confirm understanding → get scored → practice with 5 MCQs + 2 short answers → see mastery — all grounded in the uploaded book, in a UI that looks like a study app, not a dev tool.
