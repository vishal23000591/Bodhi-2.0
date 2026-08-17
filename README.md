# Bodhi

A textbook-grounded AI tutor. Upload a PDF textbook, Bodhi extracts and
topic-maps it, and the student picks a topic, gets taught, checks their own
understanding, and practices — all answered only from that textbook.

Full design doc: [`BODHI_Technical_Architecture.md`](BODHI_Technical_Architecture.md).

## Stack

- **Backend**: FastAPI (Python), MongoDB (auth/app data), ChromaDB (local, persistent — RAG vectors)
- **Extraction**: PyMuPDF (copy-paste PDFs) with a PaddleOCR fallback (scanned PDFs)
- **LLM + embeddings**: OpenRouter (`nvidia/nemotron-3-ultra-550b-a55b:free` for chat, `nvidia/nemotron-3-embed-1b:free` for embeddings)
- **Frontend**: React + Vite, peach/warm design system from the Bodhi logo

## Prerequisites

- Python 3.11+ (tested on 3.14)
- Node 18+
- MongoDB running locally (`brew install mongodb-community` or Docker)
- An OpenRouter API key

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt   # includes requirements.txt + test tools

cp .env.example .env    # fill in OPENROUTER_API_KEY and JWT_SECRET
```

Optional — only needed for scanned/image PDFs (heavy, may not have wheels
on very new Python versions yet):

```bash
pip install -r requirements-ocr.txt
```

Start MongoDB (if not already running):

```bash
mkdir -p mongo_data
mongod --dbpath mongo_data --logpath mongo_data/mongod.log --fork --port 27017
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Run tests (mocked Mongo + OpenRouter, real local ChromaDB — no network or
API key needed):

```bash
python -m pytest
```

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env 2>/dev/null || true   # VITE_API_BASE_URL, defaults to http://localhost:8000
npm run dev      # http://localhost:5173
```

Run tests:

```bash
npm test
```

## Notes / known gaps

- **Security**: `backend/.env` holds real secrets and is gitignored — never commit it. If the OpenRouter key was ever pasted into a chat or shared elsewhere, rotate it at openrouter.ai.
- **Practice feedback timing**: the architecture doc's wireframe shows per-question feedback immediately after each MCQ click. Since correct answers are intentionally withheld from the client until submission (so they can't be inspected via devtools before answering), Bodhi instead shows all feedback on one results screen right after the last question is submitted — same information, one screen later.
- **Topic generation for very long books**: currently a single LLM call with the extracted text truncated at ~60k characters. A page-batched map-reduce (mentioned as future work in the doc, section 4) would be needed for full-length textbooks.
- **react-router-dom** has an open moderate advisory (GHSA-wrjc-x8rr-h8h6) with no 6.x fix yet — only 7.18+ resolves it, which is a breaking upgrade. Low risk for local/dev use; worth revisiting before any public deployment.
- **Mastery** is the most recent teach-back/practice score for a topic (not a rolling average) — each check is treated as the current read of understanding, per the doc's mastery thresholds (≥80 mastered, 50–79 in progress, <50 needs reteach).
# Bodhi-2.0
