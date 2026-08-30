# AI Mock Interview Feature — System Design (NVIDIA STS + Domain-Knowledge Focus)

## 1. Executive Summary & Philosophy

An interview needs to be both **factually grounded** and **conversational with minimal latency**. By utilizing **NVIDIA Speech-to-Speech (STS / Audio-to-Audio)**, the system eliminates traditional multi-step pipeline latencies (STT $\to$ LLM text $\to$ TTS audio generation), enabling direct speech input and synthesized voice output with ChromaDB RAG domain grounding.

## 2. Architecture

```
┌──────────┐   candidate speech audio   ┌────────────────────────────────────────┐
│  Client  │ ─────────────────────────► │   NVIDIA Speech-to-Speech (STS) Engine │
│  App     │ ◄───────────────────────── │   - Audio-in to Audio-out Synthesis    │
└──────────┘    synthesized AI voice    └──────────────┬─────────────────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │   RAG Knowledge Retrieval │
                                         │   - Domain Vector DB      │
                                         │   - Resume / JD Embeddings│
                                         └─────────────┬─────────────┘
                                                       │
                                                       ▼
                                         ┌───────────────────────────┐
                                         │   DeepSeek LLM Evaluator  │
                                         │   - Scoring & Metrics     │
                                         │   - Context Grounding     │
                                         └───────────────────────────┘
```

## 3. Components

| Component | Job |
|---|---|
| **NVIDIA STS (Speech-to-Speech)** | End-to-end voice processing model (NVIDIA NIM / Riva STS). Converts candidate spoken input directly into conversational AI speech responses with low latency and human-like voice synthesis. |
| **Knowledge Retrieval (RAG)** | Pulls relevant facts from a **domain knowledge base** (e.g. correct definitions, standard algorithms, best practices for target roles) plus candidate **resume/JD** content via vector similarity search (ChromaDB). |
| **LLM Evaluator (DeepSeek)** | Generates structured correctness scores, feedback, and technical depth analysis grounded in retrieved facts. |
| **Interview Engine Gateway** | FastAPI REST & WebSocket orchestrator managing turn flow and real-time streaming. |

## 4. End-to-End Flow

```
1. Candidate speaks into mic (streamed via WebSocket or uploaded via REST).
2. Knowledge Retrieval queries relevant domain facts based on current context.
3. NVIDIA STS Model processes speech turn and generates synthesized conversational voice output.
4. DeepSeek LLM evaluates answer correctness, scoring (0-10), and feedback.
5. Client receives synchronized audio output and evaluation telemetry in real time.
```
