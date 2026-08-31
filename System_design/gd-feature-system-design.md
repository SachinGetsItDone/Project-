# GD (Group Discussion) Feature — Fine-Grained System Design

## 1. Scope

This document expands the AI core shown in the reference diagram —

```
┌─────────────────────────┐   text / Question    ┌─────────────────────┐
│ DeepSeek V4 Flash        │ ───────────────────► │ WhisperModel (Local) │
│ (DeepSeek V3 fallback)   │                       │ - Speech I/O          │
│ API — text generation    │ ◄─────────────────── │                       │
└─────────────────────────┘   Human Response      └─────────────────────┘
```

into a full production system for **Module 3 — Group Discussion (GD) Environment** (AI GD / Peer GD / Hybrid GD), covering room orchestration, real-time audio, multi-agent AI participants, moderation, transcript storage, and report generation.

---

## 2. High-Level Architecture

```
┌────────────┐      WebSocket/WebRTC       ┌───────────────────────────┐
│  Mobile App │ ◄───────────────────────► │   GD Gateway (Realtime)    │
│  (User)     │                             │  - Session auth            │
└────────────┘                             │  - Audio ingest/relay      │
                                            │  - Turn-taking events      │
                                            └──────────┬─────────────────┘
                                                       │
                          ┌────────────────────────────┼────────────────────────────┐
                          │                            │                            │
                 ┌────────▼────────┐         ┌─────────▼─────────┐        ┌─────────▼─────────┐
                 │  STT Service     │         │  GD Orchestrator   │        │  TTS Service        │
                 │  (Whisper local  │         │  (Room State Machine│       │  (ElevenLabs/Google │
                 │   / self-hosted) │         │   + Moderator Logic)│       │   TTS)               │
                 └────────┬────────┘         └─────────┬─────────┘        └─────────▲─────────┘
                          │  transcript                  │  prompt                    │ audio
                          └─────────────►┌────────────────▼───────────────┐──────────┘
                                          │   LLM Gateway                    │
                                          │   Primary: DeepSeek V4 Flash API │
                                          │   Fallback: DeepSeek V3 API      │
                                          │   - AI participant responses     │
                                          │   - Moderator interjections      │
                                          │   - Counter-arguments / data pts │
                                          └────────────────┬───────────────┘
                                                            │
                                          ┌─────────────────▼─────────────────┐
                                          │  Persistence Layer                  │
                                          │  - Session DB (Postgres)            │
                                          │  - Transcript store (S3 + index)    │
                                          │  - Report generation queue (async)  │
                                          └─────────────────────────────────────┘
```

The diagram's two boxes map onto this system as:
- **"DeepSeek V4 Flash (fallback V3) — API, text generation"** → the **LLM Gateway**, reused by every AI participant and the AI moderator in a GD room.
- **"WhisperModel Local"** → split into two concerns in production: **STT** (Whisper, transcribing each speaker's live audio) feeding the LLM, and a separate **TTS Service** (ElevenLabs/Google TTS, per Module 2 spec) turning LLM text back into each AI participant's voice. The diagram's single "Text to Speech" box is treated here as STT (Whisper's actual function); TTS is a distinct downstream service so multiple AI participants can each have a distinct voice.

---

## 3. Component Breakdown

### 3.1 GD Gateway (Realtime Edge Layer)
**Responsibility:** terminate client WebSocket/WebRTC connections; the only component clients talk to directly.

| Function | Detail |
|---|---|
| Auth | Validates session JWT on connect; binds `userId` to `roomId` |
| Audio ingest | Receives Opus-encoded audio chunks (250ms frames) from the active speaker |
| Audio relay | Forwards mixed/routed audio to other human participants (Peer GD / Hybrid GD) |
| Event bus | Publishes `speak_start`, `speak_end`, `raise_hand`, `mute`, `leave` events to the Orchestrator |
| Backpressure | Drops/queues frames if Orchestrator is saturated; never blocks the socket |

### 3.2 STT Service (Whisper)
**Responsibility:** convert each participant's audio stream into text with low latency.

| Function | Detail |
|---|---|
| Deployment | Self-hosted Whisper (faster-whisper / CTranslate2, GPU pool), streaming mode with 1–2s rolling windows |
| Output | Partial transcripts (interim, for live captioning) + finalized segments (on VAD silence ≥600ms) |
| Routing | Finalized segment → GD Orchestrator, tagged with `speakerId`, `timestamp`, `confidence` |
| Fallback | Cloud STT (Deepgram/Assembly) if local Whisper pool is saturated (queue depth > threshold) |

### 3.3 GD Orchestrator (Core State Machine)
**Responsibility:** owns room state, turn-taking, and decides when/what the AI should say. This is the "brain" that wraps the LLM Gateway.

**Room State Machine:**
```
CREATED → WAITING_FOR_PARTICIPANTS → PREP (60s topic display)
        → ACTIVE (15–20 min)
            ├─ substate: OPEN_FLOOR
            ├─ substate: AI_SPEAKING
            ├─ substate: HUMAN_SPEAKING
        → WRAP_UP (last 60s, prompts for conclusion)
        → ENDED → REPORT_GENERATING → REPORT_READY
```

**Moderator decision loop (runs on every finalized transcript segment or every N seconds of silence):**
1. Append segment to rolling context window (last ~2000 tokens of transcript).
2. Run lightweight heuristics before calling the LLM (cheap, no API cost):
   - Silence > 8s → trigger `PROMPT_PARTICIPATION`
   - Single speaker share of last 3 min > 60% → trigger `INTERRUPT_DOMINATION`
   - Topic-relevance drift score (local embedding similarity vs. topic) < threshold → trigger `REDIRECT_TOPIC`
3. If a trigger fires, or an AI participant's "turn" comes up in the round-robin schedule, call the **LLM Gateway** with a structured prompt (see §4).
4. Route LLM output:
   - `type: ai_statement` → send to TTS → broadcast audio + transcript to room
   - `type: moderator_nudge` → system message (text only, optionally short TTS)
   - `type: counter_argument` / `type: data_point` → same as ai_statement, tagged for scoring

### 3.4 LLM Gateway
**Responsibility:** single choke point for all text generation, matching the reference diagram's box exactly, generalized to serve N AI participants + 1 moderator per room.

| Function | Detail |
|---|---|
| Primary model | DeepSeek V4 Flash (low-latency, streaming) |
| Fallback | DeepSeek V3, triggered on: HTTP 5xx, timeout > 4s, rate-limit (429) |
| Fallback #2 | Local cached "safe response" templates if both APIs fail (keeps room alive) |
| Request shape | `{ roomId, participantId(role), topic, transcriptWindow, instruction, responseFormat }` |
| Response shape | `{ text, intent, references[], confidence }` — `responseFormat` forces JSON so the Orchestrator can route by `intent` |
| Streaming | Token-streamed back to Orchestrator so TTS can start on first sentence (reduces perceived latency) |
| Cost control | Per-room token budget; degrade to shorter responses / less-frequent AI turns if budget exceeded |

### 3.5 TTS Service
**Responsibility:** render each AI participant's text into speech with a distinct, consistent voice.

| Function | Detail |
|---|---|
| Voice assignment | Each `AI Participant N` in a room gets a fixed `voiceId` for the session (consistency) |
| Streaming | Sentence-level chunking → stream audio back to Gateway → relay to room as soon as first chunk is ready |
| Provider | ElevenLabs (primary, higher quality) / Google TTS (fallback, cheaper + faster) |

### 3.6 Persistence Layer
| Store | Contents |
|---|---|
| Postgres (`gd_sessions`) | roomId, topic, type (AI/Peer/Hybrid), participants[], startedAt, endedAt, status |
| Postgres (`gd_transcript_segments`) | segmentId, roomId, speakerId, text, startTs, endTs, confidence, intentTag |
| S3 (`gd-audio/`) | Raw per-speaker audio (for re-scoring / dispute review), lifecycle-expired after 30 days |
| Redis | Live room state (current speaker, turn queue, silence timer) — ephemeral, source of truth only while ACTIVE |
| Report queue (SQS/Kafka) | `roomId` pushed on `ENDED` → consumed by async Report Generator |

---

## 4. LLM Prompt Contract (structured)

```json
// Request to LLM Gateway
{
  "roomId": "gd_8f21",
  "role": "ai_participant_2",
  "topic": "AI will replace jobs",
  "transcriptWindow": "...last ~2000 tokens...",
  "instruction": "trigger:INTERRUPT_DOMINATION | throw a counter-argument to the last speaker's point, cite one data point, keep under 40 words, stay on topic",
  "responseFormat": "json"
}

// Response from LLM Gateway
{
  "text": "That's a fair point, but automation displaced 20% of manufacturing jobs in the last decade while creating new roles in maintenance and oversight — so is it replacement or transformation?",
  "intent": "counter_argument",
  "references": ["manufacturing automation stats"],
  "confidence": 0.88
}
```

Moderator-only instructions (`role: moderator`) are restricted to a smaller instruction set: `PROMPT_PARTICIPATION`, `REDIRECT_TOPIC`, `TIME_WARNING`, `WRAP_UP`, `SUMMARIZE_CONCLUSION`.

---

## 5. Sequence — One AI-GD Turn Cycle

```
User speaks
   │
   ▼
GD Gateway (audio frames) ──► STT (Whisper)
                                   │ finalized segment
                                   ▼
                          GD Orchestrator
                                   │ heuristic check (silence/domination/drift)
                                   │ + round-robin schedule check
                                   ▼
                      [trigger fired] ──► LLM Gateway (DeepSeek V4 Flash)
                                   │           │ (on failure) → DeepSeek V3 fallback
                                   │           │ (on double failure) → cached template
                                   ▼           ▼
                          structured JSON response
                                   │
                                   ▼
                          TTS Service (streamed)
                                   │
                                   ▼
                          GD Gateway ──► broadcast audio + live transcript to all participants
                                   │
                                   ▼
                          gd_transcript_segments (persisted)
```

---

## 6. Multi-Agent Handling (AI GD specifics)

- Each `AI Participant N` is a distinct **role**, not a distinct process — the Orchestrator calls the LLM Gateway once per turn with a different `role`/persona in the prompt (e.g., "assertive analyst", "cautious skeptic") so participants feel distinct without running N separate model instances.
- Turn order uses weighted round-robin: base rotation among AI participants, but the moderator logic can insert an out-of-turn AI response if a domination/silence trigger fires.
- Two AI participants never speak simultaneously — Orchestrator holds a single `floor` lock per room; requests queue if the floor is occupied.

## 7. Peer GD / Hybrid GD Differences

| Aspect | AI GD | Peer GD | Hybrid GD |
|---|---|---|---|
| STT usage | Per human speaker, for AI context | Per human speaker, for transcript/report only | Both |
| LLM Gateway calls | Every AI turn | None during session (moderation only, post-hoc) | Moderator turns only |
| TTS usage | Every AI turn | None | Moderator only |
| Orchestrator role | Full conversational participant | Timer + turn/hand-raise management only | Moderator (nudges, no participant turns) |

## 8. Report Generation (async, post-`ENDED`)

1. Report worker pulls `roomId` from queue.
2. Fetches full `gd_transcript_segments`.
3. Single batched LLM call (not per-turn) with `instruction: SCORE_AND_SUMMARIZE`, producing the per-user metrics already defined in Module 3.3 (Initiation, Content Quality, Listening Skills, etc.).
4. Writes to `gd_reports` table; pushes notification to client.
5. Uses DeepSeek V3 (not V4 Flash) for this step by default — scoring is not latency-sensitive, so the cheaper/more deliberate model is preferred; V4 Flash only as a speed fallback if V3 queue is backed up.

## 9. Latency Budget (per AI turn, target)

| Stage | Target |
|---|---|
| Audio → STT final segment | ≤ 700ms after speech end (VAD-gated) |
| Orchestrator decision | ≤ 50ms (heuristics are local) |
| LLM Gateway (V4 Flash, streamed, first token) | ≤ 600ms |
| TTS first audio chunk | ≤ 400ms after first LLM sentence |
| **End-to-end (silence → AI starts speaking)** | **≤ 1.7s** |

## 10. Failure & Degradation Modes

| Failure | Behavior |
|---|---|
| DeepSeek V4 Flash down/slow | Auto-retry once, then fallback to DeepSeek V3 |
| Both DeepSeek models down | Serve cached generic prompts ("Can you expand on that point?") to keep room alive; flag session as `degraded` |
| Whisper pool saturated | Fallback to cloud STT provider; increase VAD silence threshold to reduce call volume |
| TTS provider down | Fallback provider; if both down, display AI response as text-only bubble (no audio) |
| Room orchestrator crash mid-session | Redis-persisted room state allows a new Orchestrator instance to resume without losing turn order |

## 11. Moderation & Safety

- All LLM outputs pass through a lightweight content filter (toxicity/PII) before TTS — rejected outputs are regenerated once, then replaced with a safe fallback line.
- Human speech transcripts are also scanned; abusive language triggers a moderator nudge, not automatic removal, unless a repeat-offense threshold is hit (then a human-review flag is raised).

## 12. Open Questions for Engineering Review

- Should AI participant "voices" persist across sessions per user (personalization) or be randomized per room?
- Token budget per room — fixed cap vs. tiered by subscription plan?
- Do Peer GD sessions need live AI moderation at all, or only post-session scoring, to reduce cost?
