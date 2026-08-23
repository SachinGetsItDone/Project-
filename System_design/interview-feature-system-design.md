# AI Mock Interview Feature — Simple System Design (Domain-Knowledge Focus)

## 1. Why this differs from GD

A GD room needs speed and personality (multiple AI voices, quick back-and-forth). An interview needs to be **factually correct** — if the AI asks a technical question or judges a technical answer, it has to be grounded in real domain knowledge, not just fluent-sounding text. So the core addition here vs. the GD design is a **Knowledge Retrieval step** between the user's answer and the LLM's evaluation.

## 2. Architecture

```
┌──────────┐   audio    ┌───────────────┐   text    ┌────────────────────┐
│  Mobile  │ ─────────► │  STT (Whisper) │ ────────► │  Interview Engine    │
│  App     │            └───────────────┘            │  (Orchestrator)      │
└────▲─────┘                                          └─────────┬───────────┘
     │  audio (AI voice)                                         │
┌────┴─────┐   ◄────────────────────────────────────┐            │
│   TTS    │                                          │            │
└──────────┘                                          │            │
                                                        │            │
                          ┌────────────────────────────▼──┐         │
                          │   Knowledge Retrieval (RAG)     │◄────────┘
                          │   - Domain KB (vector DB)        │
                          │   - JD / Resume embeddings        │
                          └────────────────────────────┬──────┘
                                                          │ retrieved facts
                                                          ▼
                                          ┌─────────────────────────────┐
                                          │   LLM Gateway                  │
                                          │   Primary: DeepSeek V4 Flash   │
                                          │   Fallback: DeepSeek V3        │
                                          │   - Next question                │
                                          │   - Answer evaluation (grounded)│
                                          └─────────────────────────────┘
```

## 3. Components (kept minimal)

| Component | Job |
|---|---|
| **STT (Whisper)** | Converts the user's spoken answer to text |
| **Knowledge Retrieval (RAG)** | Before asking a question or scoring an answer, pulls relevant facts from a **domain knowledge base** (e.g. correct definitions, standard algorithms, best practices for the user's target role) plus the user's own **resume/JD** content, via vector similarity search |
| **LLM Gateway** | Same DeepSeek V4 Flash → V3 fallback pattern as GD. Takes the retrieved facts + transcript and generates the next question or scores the last answer — grounded in retrieved facts instead of the model's raw memory |
| **TTS** | Speaks the AI interviewer's question aloud |
| **Interview Engine** | Simple sequential flow (not multi-agent): ask → listen → retrieve → evaluate → next question |

## 4. Why RAG matters here specifically

- Prevents the AI from confidently asking outdated or wrong technical questions (e.g. deprecated library APIs, incorrect algorithm complexity).
- Lets the "AI Ideal Answer" and feedback (from Module 2.3's Post-Interview Report) be checked against real reference material instead of the LLM inventing an answer.
- Domain KB can be scoped per `Interview Type` (Technical / HR / Behavioral) and per role (e.g. Software Engineer vs. Marketing Manager) so retrieval stays relevant.

## 5. Simple Flow

```
1. User answer transcribed (STT)
2. Orchestrator queries Knowledge Retrieval:
     - "facts relevant to this question + this answer"
3. LLM Gateway call:
     input = { question, user_answer, retrieved_facts, resume/JD context }
     output = { correctness_score, feedback, next_question }
4. TTS speaks next_question
5. Repeat until interview duration ends
```

## 6. What's deliberately left out (vs. GD design)

- No multi-participant turn-taking / floor-locking (single AI ↔ single user)
- No real-time moderation triggers (silence/domination logic) — just a simple timer per question
- No per-participant voice assignment — one consistent interviewer voice
- Report generation can run synchronously at the end (no async queue needed) since it's a single transcript, not a multi-speaker one

## 7. Fallback behavior

Same as GD: DeepSeek V4 Flash → DeepSeek V3 on failure. If Knowledge Retrieval is unavailable, the Orchestrator falls back to ungrounded LLM generation but flags the session's feedback as `low_confidence` so the report can note it may need manual review.
