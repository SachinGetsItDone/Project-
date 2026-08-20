from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import json

from services.stt_service import STTService
from services.rag_service import RAGService
from services.llm_gateway import LLMGateway
from services.tts_service import TTSService

app = FastAPI(title="Mock Interview Engine Gateway")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Services
# We initialize them lazily or on startup. For simplicity, initialize on module load.
stt_service = STTService()
rag_service = RAGService()
llm_gateway = LLMGateway()
tts_service = TTSService()

@app.post("/api/interview/turn")
async def process_interview_turn_rest(
    audio_file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    resume_context: str = Form("Candidate applying for Software Engineer role.")
):
    """
    REST endpoint to process a single interview turn.
    Either audio_file OR transcript must be provided.
    """
    user_text = transcript
    if audio_file:
        # In a real scenario, convert uploaded bytes to numpy array for STT
        # audio_bytes = await audio_file.read()
        # audio_array = convert_to_numpy(audio_bytes)
        # user_text = stt_service.transcribe(audio_array)
        user_text = "Simulated transcribed text from audio."
    
    if not user_text:
        return {"error": "Provide either audio_file or transcript."}

    # 1. Retrieve Knowledge
    facts = rag_service.retrieve_facts(user_text)

    # 2. LLM Generation
    llm_response = await llm_gateway.evaluate_and_generate_next(
        transcript=user_text,
        retrieved_facts=facts,
        resume_context=resume_context
    )

    # 3. TTS Generation
    next_question = llm_response.get("next_question", "")
    tts_audio_bytes = await tts_service.generate_speech(next_question)

    return {
        "user_transcript": user_text,
        "evaluation": llm_response,
        "tts_audio_length": len(tts_audio_bytes)
    }

@app.websocket("/ws/interview")
async def websocket_interview_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time interaction.
    """
    await websocket.accept()
    resume_context = "Candidate applying for Software Engineer role."
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Simple assumption: client sends text for now, instead of binary audio
            # In a real system, we'd receive binary Opus/PCM frames, buffer them, and run VAD.
            
            # 1. RAG
            facts = rag_service.retrieve_facts(data)
            
            # 2. LLM
            llm_response = await llm_gateway.evaluate_and_generate_next(
                transcript=data,
                retrieved_facts=facts,
                resume_context=resume_context
            )
            
            # 3. TTS
            next_question = llm_response.get("next_question", "")
            tts_audio = await tts_service.generate_speech(next_question)
            
            # Send back the JSON response
            await websocket.send_text(json.dumps({
                "evaluation": llm_response,
                "has_audio": len(tts_audio) > 0
            }))
            
            # In a real app, we'd send the binary audio stream back here
            # await websocket.send_bytes(tts_audio)
            
    except WebSocketDisconnect:
        print("Client disconnected")

@app.get("/")
def read_root():
    return {"message": "Mock Interview Engine API is running"}
