from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json
import base64

from services.nvidia_sts_service import NVIDIASTSService
from services.rag_service import RAGService
from services.llm_gateway import LLMGateway

# Globals for services
nvidia_sts_service: Optional[NVIDIASTSService] = None
rag_service: Optional[RAGService] = None
llm_gateway: Optional[LLMGateway] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global nvidia_sts_service, rag_service, llm_gateway
    print("Initializing NVIDIA STS and AI Services...")
    nvidia_sts_service = NVIDIASTSService()
    rag_service = RAGService()
    llm_gateway = LLMGateway()
    print("NVIDIA STS Model & AI Services initialized successfully.")
    yield
    print("Shutting down NVIDIA STS & AI Services...")
    nvidia_sts_service = None
    rag_service = None
    llm_gateway = None

app = FastAPI(
    title="Mock Interview & GD Engine - NVIDIA STS Gateway",
    description="End-to-end Speech-to-Speech AI Mock Interview and Group Discussion Engine powered by NVIDIA STS.",
    version="2.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/interview/turn")
async def process_interview_turn_rest(
    audio_file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    resume_context: str = Form("Candidate applying for Software Engineer role.")
):
    """
    REST endpoint to process a single interview turn using NVIDIA Speech-to-Speech (STS).
    Accepts speech audio file directly or text transcript fallback.
    """
    if not audio_file and not transcript:
        return {"error": "Provide either audio_file or transcript."}

    audio_bytes = None
    if audio_file:
        audio_bytes = await audio_file.read()

    # 1. Retrieve Knowledge Facts for the context
    search_query = transcript or "Technical Interview domain concepts and system design"
    facts = rag_service.retrieve_facts(search_query) if rag_service else ""

    # 2. Process turn with NVIDIA STS model
    sts_result = await nvidia_sts_service.process_speech_turn(
        audio_bytes=audio_bytes,
        text_prompt=transcript,
        context=f"Domain Facts:\n{facts}\n\nCandidate Resume Context:\n{resume_context}",
        system_prompt="You are an expert AI technical interviewer. Evaluate the candidate's response concisely and ask the next pertinent technical question."
    )

    # 3. LLM Evaluation (scoring, feedback, structured next question)
    user_transcript = sts_result.get("transcript", transcript or "")
    llm_response = await llm_gateway.evaluate_and_generate_next(
        transcript=user_transcript,
        retrieved_facts=facts,
        resume_context=resume_context
    )

    audio_out_bytes = sts_result.get("audio_bytes", b"")
    audio_base64 = base64.b64encode(audio_out_bytes).decode("utf-8") if audio_out_bytes else ""

    return {
        "user_transcript": user_transcript,
        "evaluation": llm_response,
        "sts_model": sts_result.get("model", "nvidia-sts"),
        "sts_latency_ms": sts_result.get("latency_ms", 0),
        "sts_audio_length": len(audio_out_bytes),
        "sts_audio_base64": audio_base64
    }

@app.websocket("/ws/interview")
async def websocket_interview_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time Speech-to-Speech (STS) interaction.
    Receives candidate audio stream / messages and streams back NVIDIA STS speech responses.
    """
    await websocket.accept()
    resume_context = "Candidate applying for Software Engineer role."
    
    try:
        while True:
            # Handle incoming WebSocket message (JSON metadata or text/audio prompt)
            raw_data = await websocket.receive_text()
            
            try:
                msg = json.loads(raw_data)
                user_text = msg.get("text", "")
                incoming_audio_b64 = msg.get("audio_base64", None)
                incoming_audio = base64.b64decode(incoming_audio_b64) if incoming_audio_b64 else None
            except json.JSONDecodeError:
                user_text = raw_data
                incoming_audio = None

            # 1. RAG Domain Knowledge Retrieval
            facts = rag_service.retrieve_facts(user_text) if rag_service else ""

            # 2. NVIDIA STS Speech-to-Speech Turn
            sts_result = await nvidia_sts_service.process_speech_turn(
                audio_bytes=incoming_audio,
                text_prompt=user_text,
                context=f"{facts}\n{resume_context}"
            )

            # 3. LLM Evaluation
            candidate_transcript = sts_result.get("transcript", user_text)
            llm_response = await llm_gateway.evaluate_and_generate_next(
                transcript=candidate_transcript,
                retrieved_facts=facts,
                resume_context=resume_context
            )

            speech_bytes = sts_result.get("audio_bytes", b"")
            speech_b64 = base64.b64encode(speech_bytes).decode("utf-8") if speech_bytes else ""

            # Send back the unified STS JSON response
            await websocket.send_text(json.dumps({
                "candidate_transcript": candidate_transcript,
                "evaluation": llm_response,
                "sts_model": sts_result.get("model", "nvidia-sts"),
                "sts_latency_ms": sts_result.get("latency_ms", 0),
                "has_audio": len(speech_bytes) > 0,
                "audio_base64": speech_b64
            }))

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")

@app.get("/")
def read_root():
    return {
        "message": "Mock Interview Engine API is running",
        "engine": "NVIDIA STS (Speech-to-Speech)",
        "version": "2.0.0"
    }
