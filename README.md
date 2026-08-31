# AI Mock-Interview & GD Practice Engine

Speech-to-speech mock interviews with live scored feedback. Frontend is a React + Vite app in `client/`; backend is FastAPI in `server/`.

## Stack

| Layer        | Tech                                                       |
|--------------|------------------------------------------------------------|
| Frontend     | React 18 + Vite + react-router (Google OAuth via `@react-oauth/google`) |
| Backend      | Python / FastAPI (`server/`)                               |
| App data     | MongoDB (Motor) — interviews, turns, reports               |
| RAG          | Postgres + pgvector — domain-knowledge facts, local embeddings (`all-MiniLM-L6-v2`, no API key) |
| Reasoning    | DeepSeek (`openai` SDK, JSON mode) — scoring, next question, JD analysis, report |
| Speech       | NVIDIA STS abstraction with an honest offline fallback     |

> Note: this is FastAPI + Mongo + Postgres — not literally MERN (no Node/Express). Two databases by design.

## Quick start

```bash
# 1. Databases (Postgres+pgvector, MongoDB)
#    RAG store: either `docker compose up -d` (postgres) or a hosted
#    Supabase URL in server/.env (pgvector is built in; password with a
#    trailing '@' is written as %40). Seed is idempotent either way.
#    MongoDB: still required for interview/turn/report persistence.
docker compose up -d

# 2. Backend
cd server
python -m venv .venv                    # or reuse the repo's .venv
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m db.seed_domain_knowledge   # idempotent seed for pgvector
.venv/Scripts/python -m uvicorn main:app --reload --port 8000

# 3. Frontend
cd ../client
npm install
npm run dev        # http://localhost:5173  (proxies /api and /ws → :8000)

# 4. Run tests
cd ../server && .venv/Scripts/python -m pytest tests/ -q
```

## End-to-end flow

1. Open the app, sign in with Google (`VITE_GOOGLE_CLIENT_ID` in `client/.env`, optional).
2. Set up an interview: paste a job description + upload a resume (optional).
   - `POST /api/resume/parse` extracts resume text (PDF via `pypdf`, or TXT/MD).
   - `POST /api/jd/analyze` turns the JD into `{ role, key_skills[], focus_areas[] }`.
   - `POST /api/interviews` creates the interview + authors the opening question.
3. Live call: answer by text or microphone (`MediaRecorder`), each turn hits
   `POST /api/interview/turn`, which scores via DeepSeek, persists to Mongo, and
   returns interviewer audio synthesized **from the same next-question text** shown
   on screen (so audio and text always agree).
4. End → `POST /api/interviews/{id}/report` generates a structured report
   (overall score, competencies, strengths, gaps), stored on the interview doc.

## Configuration

Copy `server/.env.example` → `server/.env` and `client/.env.example` →
`client/.env`. Everything has a working default; you only *must* set keys to get
real LLM/audio:

| Variable                | Effect                                             |
|-------------------------|----------------------------------------------------|
| `DEEPSEEK_API_KEY`      | Real scoring / question / JD / report text. Without it the gateway falls back to canned scores + a locally-computed report. |
| `NVIDIA_API_KEY`        | Real speech synthesis. Without it the interviewer audio is a synthetic tone (honestly labeled `synthetic-audio-fallback`). |
| `DATABASE_URL`          | pgvector connection (default matches docker-compose). |
| `MONGO_URI` / `MONGO_DB`| Mongo connection (default matches docker-compose). |
| `VITE_GOOGLE_CLIENT_ID` | Real Google sign-in button. |

## Speech handling & honesty

The pipeline is a single speech-to-speech abstraction (`services/nvidia_sts_service.py`)
with three honest behaviors:

- **No `NVIDIA_API_KEY`** → candidate transcription falls back to the submitted
  transcript (or a canned line), and interviewer audio is a duration-scaled
  synthetic tone. The `sts_model` field reports `synthetic-audio-fallback`,
  never a fake "nvidia-sts" label.
- **With a key** → the provider is called; on any error it degrades to the same
  synthetic fallback and says so.
- **Coherence** → interviewer audio is always generated from the exact
  next-question text DeepSeek authored, so what's spoken matches what's shown.

## Project layout

```
project-/
├── client/            React + Vite (src/{pages,components,context,api,styles})
├── server/            FastAPI (core/, services/, db/, tests/, scripts/)
│   ├── core/gateway.py        all HTTP + WS endpoints
│   ├── services/              llm_gateway, rag_service, nvidia_sts_service,
│   │                          resume_service, jd_service
│   ├── db/                    mongo.py, pg.py, seed_domain_knowledge.py
│   └── scripts/               manual S2S model setup / smoke helpers
├── docker-compose.yml  postgres(pgvector) + mongo
└── docs/ · System_design/
```

## Known caveats / next steps

- The pgvector RAG store is verified live against a hosted Supabase Postgres in
  this repo's `server/.env`. **MongoDB is the remaining live-dependency**: the
  interview/turn/report endpoints persist only once Mongo is reachable
  (`docker compose up -d mongo`, or a hosted Mongo URI in `MONGO_URI`).
- Resume + JD-analysis adapters are generic; a richer implementation may be
  merged in from a sibling project.
- Backend Google-OAuth is client-gated only; the backend does not yet verify the
  access token (JWT verification is the documented next step).
- The `nvidia/speech-to-speech` provider endpoint is unverified — the abstraction
  is pluggable and always degrades honestly.
- Committed clutter (`__pycache__`, `data/`, `graphify-out/`) was untracked;
  the superseded root `install_s2s_model.py` can be deleted at any time.