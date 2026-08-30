# Real-Time AI Speech-to-Speech Mock Interview Platform — Design

**Status:** draft · **Date:** 2026-08-30 · **Scale target:** ≤100 concurrent interviews (idealized design)
**Stack:** MERN (MongoDB · Express · React · Node) + WebSockets + Redis (state/queue/pub-sub) + DeepSeek worker queue + external S2S model service

> This is an *idealized* whiteboard design, not a description of the current repository.
> The existing code is FastAPI (Python) + a single NVIDIA Speech-to-Speech model + ChromaDB RAG + a React front end.
> Where this design diverges from that code, it is naming the *target*, not the built system.

---

## 1. Context & the central tension

A mock-interview platform holds a spoken conversation with a candidate: the candidate hears an AI
interviewer ask a question, answers out loud, and the interviewer reacts and asks a follow-up. At the
end the candidate gets a scored report.

The load-bearing tension in the prompt is **"real-time speech-to-speech" vs "DeepSeek worker queue."**
Live conversation wants sub-second turn latency; a worker queue deliberately *adds* latency by decoupling
producer from consumer. The two only coexist if they are on **different paths**. The design resolves it by
splitting the system into two planes:

- **Live plane (synchronous, low-latency):** a true audio→audio **S2S model** carries the spoken
  conversation. No queue, no text LLM on this path.
- **Reasoning plane (asynchronous, off the hot path):** **DeepSeek** runs behind a Redis-backed work queue
  to score each answer, plan the next question, and generate the final report. It runs in the natural gaps
  between turns (candidate think/speak time), so its latency is hidden.

This split is the whole design. Everything else supports it.

## 2. Requirements

### Functional (in scope)
- Candidate authenticates and starts a mock interview (role / difficulty / topic).
- Real-time spoken dialogue: candidate audio in, interviewer audio out, with live captions.
- Per-answer scoring against a rubric and adaptive next-question selection.
- Final report: per-competency scores, strengths/gaps, transcript.
- Interview history and report retrieval.

### Non-functional
- **Turn latency:** relaxed — 1–3 s to first interviewer audio is acceptable (per stakeholder decision).
- **Scale:** ≤100 concurrent interviews, single region.
- **Availability:** best-effort; a dropped connection must be resumable, an interview must not lose scored turns.
- **Consistency:** transcript + scores are durable (must not lose a scored turn); live session state is
  rebuildable from the transcript, so it may be eventually consistent.
- **Cost:** dominated by the S2S GPU streams and DeepSeek tokens — the design must cap concurrency, not
  buffer demand infinitely.

### Out of scope (this pass)
- Multi-region / geo-failover, multi-tenant isolation, billing.
- Human interviewers, video, screen-share, collaborative coding pad.
- >100 concurrent (the §9 evolution note says what changes at 10×).

### Assumptions
- Avg interview ≈ 20 min, ≈ 2 turns/min ⇒ ≈ 40 turns/interview.
- One active interview per user (admission control enforces it).
- S2S is a hosted/GPU service billed per concurrent stream; DeepSeek is a hosted text LLM billed per token.
- Audio is Opus-encoded on the client; raw audio is not persisted unless a "record" option is on.

## 3. Back-of-the-envelope

| Quantity | Chain | Result | Consequence |
|---|---|---|---|
| Concurrent S2S streams | = concurrent interviews | **100** | Hard ceiling. GPU-bound, the cost driver and first thing to saturate. |
| Scoring jobs/sec (peak) | 100 int × 2 turns/min ÷ 60 | **≈ 3.3/s** | Tiny rate; sizing is about *latency*, not throughput. |
| Workers needed | 3.3 job/s ÷ (1 job / ~2 s) | **≈ 7**, round to **10** | One small autoscaled pool. |
| Mongo write rate | ~2 writes/turn × 3.3 turn/s | **≈ 7/s** | ≪ 1k QPS single-node ceiling. One node + replica. |
| Storage/interview | 40 turns × ~0.5 KB text + scores | **~50 KB** | ~40 MB/day; ~15 GB/year. Trivial. Audio blobs excluded. |
| Redis footprint | 100 sessions × few KB | **< 1 MB** state | One instance covers state + queue + pub/sub. It becomes the SPOF (§8). |
| Audio bandwidth | Opus ~64 kbps × 100 streams | **~6.4 Mbps** | Not a constraint. |

**Reading:** at this scale, nothing except the S2S GPU capacity is close to a limit. The design should be
*simple* and spend its complexity budget on (a) admission control for the S2S ceiling and (b) not losing
scored turns — not on sharding or multi-region.

## 4. High-level design

Four data flows over the two planes:

**Flow A — Auth & session setup (REST/HTTPS)**
React → LB → Express API → MongoDB. Creates the interview session (role, rubric, question bank), returns
`session_id` + a short-lived WebSocket ticket.

**Flow B — Live interview (WebSocket + S2S) — the live plane**
React captures mic (Opus) → WS → Node gateway → **S2S model service** (streaming audio in) → interviewer
audio streams back → WS → React playback + captions. The gateway steers the S2S turn with the *current
question text + interviewer persona* it reads from Redis, and writes turn boundaries + running transcript
back to Redis session state. **No queue and no DeepSeek on this path.**

**Flow C — Reasoning (async work queue) — the reasoning plane**
On an answer-complete turn boundary, the gateway enqueues a `score+plan` job `{session_id, turn_index,
transcript}` to Redis/BullMQ. A **DeepSeek worker** pulls context (transcript + rubric + RAG facts from the
vector store), calls DeepSeek, and produces `{score, feedback, next_question}`. It appends the score to
Mongo, writes `next_question` into Redis session state, then **publishes `result-ready` on Redis pub/sub**.
The gateway instance that owns that WebSocket receives the pub/sub message and pushes a live score chip to
the client and arms the next question for the S2S layer.

**Flow D — Final report (async, low-priority queue)**
On interview end, the gateway enqueues a `report` job. A worker aggregates all turns from Mongo, calls
DeepSeek to summarize, writes the report doc to Mongo, and notifies the client (over WS if still connected,
else the client fetches it later via REST).

### Components
- **React SPA** — mic capture, audio playback, live captions, report view.
- **Load balancer (L7, WebSocket-aware, sticky)** — session affinity so a WS stays pinned to one Node instance.
- **Node + Express (WS gateway + REST API)** — 1–2 instances for HA, not capacity.
- **S2S model service (GPU)** — external/hosted; the live audio↔audio brain-stem. *The bottleneck.*
- **Redis** — three roles: live session state (KV), BullMQ work + report queues, and pub/sub for result fan-out to the owning WS node.
- **DeepSeek worker pool (BullMQ consumers)** — ~10 workers; call DeepSeek + vector store.
- **DeepSeek API** — the reasoning LLM (scoring, planning, report).
- **MongoDB (primary + replica)** — users, sessions, transcripts, scores, reports, question bank.
- **Vector store (RAG)** — domain knowledge that grounds follow-up questions (Mongo Atlas Vector Search keeps it in-stack; a dedicated store is the alternative).
- **DLQ** — poison scoring jobs after capped retries.
- **Object store (optional)** — audio recordings if "record" is enabled; never store audio blobs in Mongo.

## 5. API sketch (concrete interfaces)

REST (HTTPS):
```
POST /api/auth/login                 → { token }
POST /api/interviews                 { role, difficulty, topic }
                                     → { session_id, ws_ticket }        # ticket is short-lived, single-use
GET  /api/interviews/:id             → { status, turns[], scores[] }
GET  /api/interviews/:id/report      → { competencies[], summary, transcript }
GET  /api/interviews?user=me         → { sessions[] }                   # paginated (cursor)
```

WebSocket (`wss://…/interview?ticket=…`), message envelope:
```jsonc
// client → server
{ "t": "audio",      "seq": 128, "codec": "opus", "data": "<base64|binary>" }
{ "t": "turn_end",   "turn_index": 7 }                 // client- or VAD-detected end of answer
// server → client
{ "t": "audio",      "seq": 340, "data": "<binary>" }  // interviewer speech
{ "t": "caption",    "final": false, "text": "so tell me about…" }
{ "t": "score",      "turn_index": 6, "score": 0.72, "feedback": "…" }  // arrives async, out of turn
{ "t": "state",      "phase": "listening|thinking|speaking" }
```

Queue message (Redis/BullMQ) — a message is a contract:
```jsonc
{
  "message_id": "uuid",          // dedup key (at-least-once)
  "type": "score_plan | report",
  "session_id": "…",             // ordering / partition key (per-session FIFO)
  "turn_index": 7,               // idempotency: (session_id, turn_index) is unique
  "schema_version": 1,
  "trace_id": "…",
  "payload": { "transcript_segment": "…", "rubric_id": "…" }
}
```

## 6. Data model (MongoDB)

- `users` — `{ _id, email, name, auth_provider }`
- `sessions` — `{ _id, user_id, role, difficulty, status, current_turn, started_at, ended_at }`
- `turns` — `{ _id, session_id, turn_index, transcript, question_asked, answer, score, feedback, created_at }`
  - unique index `(session_id, turn_index)` — enforces idempotent scoring under at-least-once delivery.
- `reports` — `{ _id, session_id, competencies[], summary, generated_at }`
- `question_bank` — `{ _id, role, difficulty, text, competency, follow_ups[] }` — fallback source when DeepSeek is saturated.

Redis keys (ephemeral, TTL'd):
- `sess:{id}:state` → hash `{ current_question, turn_index, persona, phase }`
- `sess:{id}:conn` → which gateway instance owns the WS (for pub/sub routing)
- BullMQ lists/streams for `score_plan`, `report`, and their DLQs.

## 7. Trade-offs (solves / worsens / when-to-change)

**S2S model on the live path (vs STT→DeepSeek→TTS pipeline)**
- *Solves:* natural turn-taking and lowest conversational latency; one component owns the audio.
- *Worsens:* content control — a black-box audio→audio model is harder to steer to an exact question; GPU cost per concurrent stream; vendor lock-in.
- *Change it when:* you need fine-grained control of every word the interviewer says, or S2S stream cost dominates → switch the live plane to STT→(small fast LLM)→TTS and keep DeepSeek async.

**DeepSeek behind a work queue, off the live path (vs inline on the turn)**
- *Solves:* the real-time tension — the live conversation never blocks on a 1–3 s LLM call; workers scale to drain bursts; a slow/failed LLM degrades gracefully to a question-bank default.
- *Worsens:* scoring is eventually consistent (the score chip arrives a beat after the answer); at-least-once delivery means duplicates ⇒ consumers must be idempotent.
- *Change it when:* the *next question* must be DeepSeek-authored with zero fallback and latency budget shrinks → precompute candidate questions one turn ahead, or move to a streaming inline call.

**Redis as state + queue + pub/sub (vs separate systems)**
- *Solves:* one dependency covers three needs at this scale; sub-ms state reads; BullMQ is batteries-included.
- *Worsens:* single point of failure; conflates three concerns on one box.
- *Change it when:* scale or blast-radius concerns grow → split the queue onto a dedicated broker, add Redis replicas/Sentinel or managed Redis.

**MongoDB (vs SQL)**
- *Solves:* flexible transcript/turn/report documents; the write and storage rates are trivial for one node; in-stack (MERN) and offers vector search.
- *Worsens:* cross-document transactions and strong relational integrity are weaker.
- *Change it when:* reporting needs heavy relational analytics → add an OLAP export; the model is not the constraint at this scale.

**Sticky WebSocket routing (vs stateless)**
- *Solves:* a long-lived audio socket stays on one instance; pub/sub only needs to notify the owning node.
- *Worsens:* uneven load if one instance gets the long interviews; a lost instance drops its live sockets.
- *Change it when:* instance count grows → a Redis-backed connection registry lets any node route to the owner.

## 8. Failure modes & resilience

| Failure | Effect | Mitigation |
|---|---|---|
| **S2S service saturated** (100-stream ceiling hit) | New interviews can't get an audio stream | **Admission control**: waitlist / "try again shortly" at start; one active session per user; alarm on stream utilization. Never queue live audio. |
| **DeepSeek slow or down** | Scores + next question delayed | Live plane continues; gateway serves the **next question from the question bank** as fallback; scores backfill when the worker recovers. Two queues so reports never starve live scoring. |
| **Poison scoring job** (always fails) | Worker capacity burned, per-session backlog | Capped retries with backoff+jitter → **DLQ**; session proceeds with fallback question; human inspects DLQ. |
| **Redis down** (SPOF) | Live state + queues + pub/sub lost | AOF persistence + replica (Sentinel); session state is **rebuildable from Mongo turns**; on restart, reload state from the last persisted turn. |
| **WebSocket drop / reconnect storm** | Candidate loses audio mid-interview | Client resumes with `session_id`; gateway restores `sess:*:state` from Redis (or Mongo); idempotent turn indices prevent double-scoring on replay. |
| **Duplicate queue delivery** (at-least-once) | Same answer scored twice | Idempotency on `(session_id, turn_index)` unique index; `message_id` dedup. |
| **Mongo primary failover** | Brief write unavailability | Replica set with automatic failover; workers retry writes with backoff. |
| **Backlog growth** (workers can't keep up) | Score latency climbs invisibly | **Bounded queue + backpressure**; alarm on **oldest-message age / consumer lag** (not just rate); autoscale workers; shed to fallback question. |

## 9. Bottlenecks & evolution (what changes at the next order of magnitude)

**Current bottleneck (ranked):**
1. **S2S GPU stream capacity** — the 100-stream ceiling. It caps concurrency and dominates cost. Admission control is the release valve, not more buffering.
2. **DeepSeek turn latency under burst** — fine at 3.3 job/s with think-time gaps; watch consumer lag if many interviews hit turn boundaries together.
3. **Redis blast radius** — one instance is three SPOFs in a trench coat.
4. **WS instance affinity** — a lost gateway drops its live interviews.

**At 10× (≈1,000 concurrent):**
- S2S: negotiate provider quota or stand up a **GPU worker fleet** with its own admission queue; stream cost becomes the line item to optimize (consider switching the live plane to STT→small-LLM→TTS).
- Node/WS: many instances behind the LB; replace sticky-only routing with a **Redis-backed connection registry** so pub/sub can reach any owner; consider a dedicated WS tier separate from the REST API.
- Redis: split roles — managed Redis (Sentinel/Cluster) for state, a **dedicated broker** for the queue.
- Mongo: still comfortable; add read replicas for report/history reads; shard only if history retention explodes.
- Add **observability** first (metrics/traces/SLOs, queue-depth + oldest-message-age alarms) — you can't scale what you can't see.

**At 100× / multi-region:** geo-route clients to the nearest region (S2S latency is physical); regional Redis + Mongo with async cross-region replication for history; the live plane stays regional, the reasoning/report plane can be centralized.

## 10. Scorecard & weakest dimension

Rated against the quality bar (clarify → quantify → justify → design-for-failure → concrete interfaces → hypothesis-not-dogma):

- **Requirements & scope:** strong — functional/non-functional/out-of-scope explicit, assumptions stated.
- **Quantification:** strong — every component checked against a number; the S2S ceiling is derived, not asserted.
- **Justification:** strong — each major choice has solves/worsens/when-to-change.
- **Failure design:** strong — SPOFs named, degradation story is concrete (fallback question, rebuild-from-Mongo).
- **Concrete interfaces:** good — REST, WS envelope, queue contract, primary keys all written.
- **Weakest dimension → the S2S model itself.** It is treated as a well-behaved external box, but it is
  simultaneously the bottleneck, the cost driver, *and* the hardest thing to steer (content control) and
  test (failure behavior of a hosted audio model is opaque). **What would raise it:** a spike / load test of
  the S2S provider to find the real concurrent-stream limit and tail latency, plus a proven fallback (the
  STT→small-LLM→TTS pipeline) so the live plane is not single-vendor. Until that exists, the design is a
  hypothesis resting on an unmeasured dependency.

**Not perfect:** the design is right-sized for ≤100 concurrent and will need the §9 changes before 1,000.
The one thing to measure next is the S2S provider's true ceiling and failure behavior.
