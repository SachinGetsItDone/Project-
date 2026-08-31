"""FastAPI gateway for the mock-interview engine.

This module is the single request entry point. It wires the four services
(Speech-to-Speech, RAG, DeepSeek reasoning, JD analysis) into HTTP endpoints
and persists application data (interviews + turns) in MongoDB.

Endpoints
---------
- ``POST /api/interviews``            — create an interview (+ JD analysis, opening question)
- ``POST /api/interview/turn``        — process one turn (audio/text) and persist it
- ``POST /api/interviews/{id}/report``— write the post-interview report
- ``GET  /api/interviews/{id}``       — fetch an interview
- ``GET  /api/interviews/{id}/report``— fetch a stored report
- ``POST /api/resume/parse``          — extract plain text from an uploaded resume
- ``POST /api/jd/analyze``            — turn a job description into structured skills
- ``WS   /ws/interview``              — real-time streaming variant of the turn

DB access is best-effort: if Mongo/Postgres are down the endpoints still answer
(RAG returns an empty fact set, turns are not persisted) so local development
stays usable without docker.
"""

import base64
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import mongo
from db.pg import close_pool as close_pg_pool
from db.pg import init_schema as init_pg_schema
from services.jd_service import JDService
from services.llm_gateway import LLMGateway
from services.nvidia_sts_service import NVIDIASTSService
from services.rag_service import RAGService
from services.resume_service import extract_text

# Global service singletons (lazy, so importing this module needs no credentials).
_nvidia_sts_service: Optional[NVIDIASTSService] = None
_rag_service: Optional[RAGService] = None
_llm_gateway: Optional[LLMGateway] = None
_jd_service: Optional[JDService] = None


def get_sts_service() -> NVIDIASTSService:
    global _nvidia_sts_service
    if _nvidia_sts_service is None:
        _nvidia_sts_service = NVIDIASTSService()
    return _nvidia_sts_service


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service


def get_llm_gateway() -> LLMGateway:
    global _llm_gateway
    if _llm_gateway is None:
        _llm_gateway = LLMGateway()
    return _llm_gateway


def get_jd_service() -> JDService:
    global _jd_service
    if _jd_service is None:
        _jd_service = JDService(get_llm_gateway())
    return _jd_service


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _oid(value: str) -> Optional[ObjectId]:
    try:
        return ObjectId(value)
    except Exception:
        return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing STS, RAG, LLM, and JD services...")
    get_sts_service()
    get_rag_service()
    get_llm_gateway()
    get_jd_service()

    # Both are best-effort: a missing database must not prevent the API from
    # starting (tests and first-run dev work without docker).
    try:
        init_pg_schema()
        print("Postgres / pgvector schema ready.")
    except Exception as e:
        print(f"[gateway] Postgres init skipped (is it running?): {e}")
    try:
        await mongo.init_indexes()
        print("MongoDB indexes ready.")
    except Exception as e:
        print(f"[gateway] Mongo init skipped (is it running?): {e}")

    yield

    print("Shutting down ...")
    mongo.close_client()
    close_pg_pool()


app = FastAPI(
    title="Mock Interview & GD Engine - NVIDIA STS Gateway",
    description="End-to-end Speech-to-Speech AI Mock Interview and Group Discussion Engine.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Request models
# --------------------------------------------------------------------------- #
class InterviewCreate(BaseModel):
    role: str = ""
    interview_type: str = "technical"
    jd_text: str = ""
    resume_text: str = ""
    user_id: str = "anonymous"


class JDAnalyzeRequest(BaseModel):
    jd_text: str = ""


class GameState(BaseModel):
    """Gamification state synced from the client (see GameContext.jsx)."""
    user_id: str
    xp: int = 0
    streak: int = 0
    last_practice_date: Optional[str] = None
    gems: int = 0
    hearts: int = 5
    achievements: list = []
    skill_tree: dict = {}
    league: str = "bronze"
    weekly_xp: int = 0
    weekly_start_date: Optional[str] = None
    total_interviews: int = 0


def _xp_for_score(score: int) -> int:
    """Server-side XP per turn — must match the client's InterviewCall.jsx."""
    xp = 10  # base XP per answer
    if score >= 8:
        xp += 25
    if score >= 9:
        xp += 15
    return xp


# --------------------------------------------------------------------------- #
# Interviews
# --------------------------------------------------------------------------- #
@app.post("/api/interviews")
async def create_interview(payload: InterviewCreate):
    """Create an interview: analyze the JD (if any) + author the opening question."""
    jd_analysis = None
    if (payload.jd_text or "").strip():
        try:
            jd_analysis = await get_jd_service().analyze(payload.jd_text)
        except Exception as e:
            print(f"[gateway] JD analysis failed: {e}")

    role = payload.role or ((jd_analysis or {}).get("role") or "")
    opening_question = await get_llm_gateway().generate_opening_question(
        role=role,
        jd_analysis=jd_analysis,
        resume_context=payload.resume_text,
    )

    now = _now()
    doc = {
        "user_id": payload.user_id,
        "role_target": role,
        "interview_type": payload.interview_type,
        "status": "in_progress",
        "jd_text": payload.jd_text,
        "resume_text": payload.resume_text,
        "jd_analysis": jd_analysis,
        "current_turn": 0,
        "current_question": opening_question,
        "post_interview_report": None,
        "created_at": now,
        "updated_at": now,
    }
    result = await mongo.get_db().interviews.insert_one(doc)
    print(f"[gateway] Created interview {result.inserted_id}")

    return {
        "interview_id": str(result.inserted_id),
        "role_target": role,
        "opening_question": opening_question,
        "jd_analysis": jd_analysis,
    }


async def _find_interview(interview_id: str):
    oid = _oid(interview_id)
    if oid is None:
        return None
    return await mongo.get_db().interviews.find_one({"_id": oid})


async def _persist_turn(
    interview_id: str,
    user_answer_text: str,
    retrieved_facts: str,
    correctness_score: int,
    feedback: str,
    next_question: str,
) -> Optional[int]:
    """Insert a turn (idempotent on interview_id+turn_number) and bump counters.

    Returns the turn number, or None if the interview is missing.
    """
    db = mongo.get_db()
    iv = await db.interviews.find_one({"_id": _oid(interview_id)})
    if iv is None:
        return None

    turn_number = int(iv.get("current_turn", 0)) + 1
    turn_doc = {
        "interview_id": ObjectId(interview_id),
        "turn_number": turn_number,
        "question_text": iv.get("current_question", ""),
        "user_answer_text": user_answer_text,
        "retrieved_facts": retrieved_facts,
        "correctness_score": correctness_score,
        "feedback": feedback,
        "next_question": next_question,
        "created_at": _now(),
    }
    await db.interview_turns.replace_one(
        {"interview_id": ObjectId(interview_id), "turn_number": turn_number},
        turn_doc,
        upsert=True,
    )
    await db.interviews.update_one(
        {"_id": ObjectId(interview_id)},
        {
            "$set": {
                "current_turn": turn_number,
                "current_question": next_question,
                "updated_at": _now(),
            }
        },
    )
    return turn_number


# --------------------------------------------------------------------------- #
# Interview turn (the core loop)
# --------------------------------------------------------------------------- #
@app.post("/api/interview/turn")
async def process_interview_turn_rest(
    audio_file: Optional[UploadFile] = File(None),
    transcript: Optional[str] = Form(None),
    interview_id: Optional[str] = Form(None),
    resume_context: str = Form("Candidate applying for Software Engineer role."),
):
    """Process a single interview turn and return score + feedback + coherent audio.

    Audio and text are accepted; at least one must be present. When an
    ``interview_id`` is supplied the turn is persisted to Mongo. The returned
    audio is synthesized from the *same next-question text the user reads*, so
    the spoken reply always matches what's on screen.
    """
    if not audio_file and not transcript:
        return {"error": "Provide either audio_file or transcript."}

    sts = get_sts_service()
    rag = get_rag_service()
    llm = get_llm_gateway()

    audio_bytes = await audio_file.read() if audio_file else None

    # If this is a real interview, prefer its stored resume text for context.
    if interview_id:
        iv = None
        oid = _oid(interview_id)
        if oid is not None:
            try:
                iv = await mongo.get_db().interviews.find_one({"_id": oid})
            except Exception:
                iv = None
        if iv and (iv.get("resume_text") or "").strip():
            resume_context = iv["resume_text"]

    # 1. Turn speech into text (STS). Falls back to the provided transcript.
    search_query = transcript or "Technical Interview domain concepts and system design"
    facts = rag.retrieve_facts(search_query) if rag else ""

    sts_result = await sts.process_speech_turn(
        audio_bytes=audio_bytes,
        text_prompt=transcript,
        context=f"Domain Facts:\n{facts}\n\nCandidate Resume Context:\n{resume_context}",
        system_prompt=(
            "You are an expert AI technical interviewer. Evaluate the candidate's "
            "response concisely and ask the next pertinent technical question."
        ),
    )
    user_transcript = sts_result.get("transcript", transcript or "")

    # 2. Score + feedback + next question (DeepSeek).
    llm_response = await llm.evaluate_and_generate_next(
        transcript=user_transcript,
        retrieved_facts=facts,
        resume_context=resume_context,
    )
    next_question = llm_response.get("next_question", "")

    # 3. Coherent interviewer audio: synthesize FROM the next question, so the
    #    spoken output and the visible question cannot diverge.
    if next_question:
        audio_out_bytes = sts.synthesize_text(next_question)
        model_label = sts.synthesize_model_label()
    else:
        audio_out_bytes = sts_result.get("audio_bytes", b"")
        model_label = sts_result.get("model", "synthetic-audio-fallback")

    audio_base64 = base64.b64encode(audio_out_bytes).decode("utf-8") if audio_out_bytes else ""

    turn_number = None
    if interview_id and _oid(interview_id) is not None:
        try:
            turn_number = await _persist_turn(
                interview_id=interview_id,
                user_answer_text=user_transcript,
                retrieved_facts=facts,
                correctness_score=int(llm_response.get("correctness_score", 0) or 0),
                feedback=llm_response.get("feedback", ""),
                next_question=next_question,
            )
        except Exception as e:
            print(f"[gateway] Turn persistence failed (continuing): {e}")

    score = int(llm_response.get("correctness_score", 0) or 0)

    return {
        "user_transcript": user_transcript,
        "evaluation": llm_response,
        "response_text": next_question,
        "turn_number": turn_number,
        "xp_earned": _xp_for_score(score),
        "sts_model": model_label,
        "sts_latency_ms": sts_result.get("latency_ms", 0),
        "sts_audio_length": len(audio_out_bytes),
        "sts_audio_base64": audio_base64,
    }


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@app.get("/api/interviews/{interview_id}")
async def get_interview(interview_id: str):
    iv = await _find_interview(interview_id)
    if iv is None:
        return {"error": "Interview not found"}
    iv["_id"] = str(iv["_id"])
    return iv


@app.post("/api/interviews/{interview_id}/report")
async def generate_interview_report(interview_id: str):
    iv = await _find_interview(interview_id)
    if iv is None:
        return {"error": "Interview not found"}

    db = mongo.get_db()
    turns = await db.interview_turns.find(
        {"interview_id": ObjectId(interview_id)}
    ).sort("turn_number", 1).to_list(200)

    try:
        report = await get_llm_gateway().generate_report(
            turns=turns,
            resume_context=iv.get("resume_text", ""),
            jd_analysis=iv.get("jd_analysis"),
        )
    except Exception as e:
        print(f"[gateway] Report generation failed: {e}")
        report = get_llm_gateway()._fallback_report(turns)

    await db.interviews.update_one(
        {"_id": ObjectId(interview_id)},
        {"$set": {"post_interview_report": report, "status": "completed", "updated_at": _now()}},
    )
    return report


@app.get("/api/interviews/{interview_id}/report")
async def get_interview_report(interview_id: str):
    iv = await _find_interview(interview_id)
    if iv is None:
        return {"error": "Interview not found"}
    return iv.get("post_interview_report") or {"detail": "Report not generated yet."}


# --------------------------------------------------------------------------- #
# Gamification: user progress + leaderboard
# --------------------------------------------------------------------------- #
@app.get("/api/user/progress")
async def get_user_progress(user_id: str):
    """Fetch a user's gamification state (XP, streak, hearts, skill tree…)."""
    doc = await mongo.get_db().user_progress.find_one({"user_id": user_id})
    if doc is None:
        return {"user_id": user_id, "exists": False}
    doc["_id"] = str(doc["_id"])
    doc["exists"] = True
    return doc


@app.post("/api/user/progress")
async def upsert_user_progress(payload: GameState):
    """Upsert the gamification state synced from the client."""
    data = payload.model_dump()
    data["level"] = int(data["xp"] // 100) + 1
    now = _now()
    data["updated_at"] = now
    result = await mongo.get_db().user_progress.replace_one(
        {"user_id": payload.user_id},
        data,
        upsert=True,
    )
    return {"user_id": payload.user_id, "updated": True, "level": data["level"], "result": str(result.upserted_id or "")}


@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 20):
    """Week's league leaderboard: users ranked by weekly XP (then total XP)."""
    cur = (
        mongo.get_db().user_progress.find({})
        .sort([("weekly_xp", -1), ("xp", -1)])
        .limit(limit)
    )
    rows = []
    rank = 1
    async for doc in cur:
        rows.append(
            {
                "rank": rank,
                "user_id": doc.get("user_id", ""),
                "name": doc.get("name") or doc.get("user_id", "Player"),
                "xp": doc.get("xp", 0),
                "weekly_xp": doc.get("weekly_xp", 0),
                "league": doc.get("league", "bronze"),
            }
        )
        rank += 1
    return {"league": "weekly", "rows": rows}


# --------------------------------------------------------------------------- #
# Resume + JD analysis
# --------------------------------------------------------------------------- #
@app.post("/api/resume/parse")
async def parse_resume(file: UploadFile = File(...)):
    data = await file.read()
    text = extract_text(file.filename or "", data)
    return {"text": text}


@app.post("/api/jd/analyze")
async def analyze_jd(payload: JDAnalyzeRequest):
    return await get_jd_service().analyze(payload.jd_text)


# --------------------------------------------------------------------------- #
# Real-time WebSocket variant
# --------------------------------------------------------------------------- #
@app.websocket("/ws/interview")
async def websocket_interview_endpoint(websocket: WebSocket):
    """Streaming STS: candidate audio/text in, coherent interviewer audio out.

    Persistence is skipped here (the REST turn endpoint is the durable path);
    this keeps the streaming loop fast and simple.
    """
    await websocket.accept()
    resume_context = "Candidate applying for Software Engineer role."
    sts = get_sts_service()
    rag = get_rag_service()
    llm = get_llm_gateway()

    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                msg = json.loads(raw_data)
                user_text = msg.get("text", "")
                incoming_audio_b64 = msg.get("audio_base64", None)
                incoming_audio = base64.b64decode(incoming_audio_b64) if incoming_audio_b64 else None
            except json.JSONDecodeError:
                user_text = raw_data
                incoming_audio = None

            facts = rag.retrieve_facts(user_text) if rag else ""
            sts_result = await sts.process_speech_turn(
                audio_bytes=incoming_audio,
                text_prompt=user_text,
                context=f"{facts}\n{resume_context}",
            )
            candidate_transcript = sts_result.get("transcript", user_text)
            llm_response = await llm.evaluate_and_generate_next(
                transcript=candidate_transcript,
                retrieved_facts=facts,
                resume_context=resume_context,
            )
            next_question = llm_response.get("next_question", "")

            # Coherent audio: speak the SAME text we send back as the question.
            if next_question:
                speech_bytes = sts.synthesize_text(next_question)
                model_label = sts.synthesize_model_label()
            else:
                speech_bytes = sts_result.get("audio_bytes", b"")
                model_label = sts_result.get("model", "synthetic-audio-fallback")

            speech_b64 = base64.b64encode(speech_bytes).decode("utf-8") if speech_bytes else ""

            await websocket.send_text(json.dumps({
                "candidate_transcript": candidate_transcript,
                "evaluation": llm_response,
                "response_text": next_question,
                "sts_model": model_label,
                "sts_latency_ms": sts_result.get("latency_ms", 0),
                "has_audio": len(speech_bytes) > 0,
                "audio_base64": speech_b64,
            }))
    except WebSocketDisconnect:
        print("WebSocket client disconnected.")


@app.get("/")
def read_root():
    return {
        "message": "Mock Interview Engine API is running",
        "engine": "NVIDIA STS (Speech-to-Speech)",
        "version": "2.0.0",
    }