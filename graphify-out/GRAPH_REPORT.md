# Graph Report - Project-  (2026-08-30)

## Corpus Check
- Corpus is ~2,883 words - fits in a single context window. You may not need a graph.

## Summary
- 117 nodes · 132 edges · 13 communities
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 3 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- React Frontend & Pages
- Speech-to-Speech (STS) Service
- Backend Gateway, LLM & RAG
- Vite Build / devDependencies
- Frontend NPM Dependencies
- DB Schema (db/)
- DB Schema (root dup)
- REST Interview-Turn Endpoint
- WebSocket STS Endpoint

## God Nodes (most connected - your core abstractions)
1. `NVIDIASTSService` - 13 edges
2. `RAGService` - 6 edges
3. `lifespan()` - 5 edges
4. `LLMGateway` - 5 edges
5. `process_interview_turn_rest()` - 4 edges
6. `scripts` - 4 edges
7. `websocket_interview_endpoint()` - 3 edges
8. `interviews` - 3 edges
9. `interviews` - 3 edges
10. `App()` - 2 edges

## Surprising Connections (you probably didn't know these)
- `lifespan()` --uses--> `NVIDIASTSService`  [INFERRED]
  core/gateway.py → services/nvidia_sts_service.py
- `lifespan()` --uses--> `LLMGateway`  [INFERRED]
  core/gateway.py → services/llm_gateway.py
- `lifespan()` --uses--> `RAGService`  [INFERRED]
  core/gateway.py → services/rag_service.py
- `test_nvidia_sts()` --calls--> `NVIDIASTSService`  [EXTRACTED]
  test_model.py → services/nvidia_sts_service.py

## Import Cycles
- None detected.

## Communities (13 total, 0 thin omitted)

### Community 0 - "React Frontend & Pages"
Cohesion: 0.08
Nodes (3): App(), ProtectedRoute(), AuthProvider()

### Community 1 - "Speech-to-Speech (STS) Service"
Cohesion: 0.15
Nodes (10): Any, NVIDIASTSService, NVIDIA Speech-to-Speech (STS) Service. Replaces standalone STT and TTS…, Process a real-time streaming audio chunk through NVIDIA STS., Generates a valid 44-byte standard RIFF WAV header for raw PCM audio., Generates clean synthesized speech PCM audio data for simulation/fallback., Process an input speech turn end-to-end using the NVIDIA STS model. Args:…, [DEPRECATED] Standalone STT Service has been completely removed. The project… (+2 more)

### Community 2 - "Backend Gateway, LLM & RAG"
Cohesion: 0.14
Nodes (10): Settings, lifespan(), read_root(), FastAPI, get, LLMGateway, Evaluate user answer and generate the next interview question. Returns JSON…, RAGService (+2 more)

### Community 3 - "Vite Build / devDependencies"
Cohesion: 0.14
Nodes (13): devDependencies, vite, @vitejs/plugin-react, name, private, scripts, build, dev (+5 more)

### Community 4 - "Frontend NPM Dependencies"
Cohesion: 0.18
Nodes (11): lucide-react, dependencies, lucide-react, react, react-dom, @react-oauth/google, react-router-dom, react (+3 more)

### Community 5 - "DB Schema (db/)"
Cohesion: 0.60
Nodes (4): domain_knowledge, interview_turns, interviews, users

### Community 6 - "DB Schema (root dup)"
Cohesion: 0.60
Nodes (4): domain_knowledge, interview_turns, interviews, users

### Community 7 - "REST Interview-Turn Endpoint"
Cohesion: 0.50
Nodes (4): process_interview_turn_rest(), REST endpoint to process a single interview turn using NVIDIA Speech-to-Speech…, post, UploadFile

### Community 9 - "WebSocket STS Endpoint"
Cohesion: 0.67
Nodes (3): WebSocket endpoint for real-time Speech-to-Speech (STS) interaction. Receives…, websocket_interview_endpoint(), websocket

## Knowledge Gaps
- **17 isolated node(s):** `Settings`, `domain_knowledge`, `name`, `private`, `version` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `NVIDIASTSService` connect `Speech-to-Speech (STS) Service` to `Backend Gateway, LLM & RAG`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `dependencies` connect `Frontend NPM Dependencies` to `Vite Build / devDependencies`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `lifespan()` (e.g. with `LLMGateway` and `NVIDIASTSService`) actually correct?**
  _`lifespan()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Settings`, `domain_knowledge`, `name` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `React Frontend & Pages` be split into smaller, more focused modules?**
  _Cohesion score 0.07635467980295567 - nodes in this community are weakly interconnected._
- **Should `Speech-to-Speech (STS) Service` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._
- **Should `Backend Gateway, LLM & RAG` be split into smaller, more focused modules?**
  _Cohesion score 0.14035087719298245 - nodes in this community are weakly interconnected._