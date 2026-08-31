"""MongoDB access (async, via Motor) for application data.

Collections:
- ``users``           — { _id, email, name, auth_provider, created_at }
- ``interviews``      — { _id, user_id, role_target, interview_type, status,
                          jd_text, resume_text, jd_analysis, current_turn,
                          current_question, post_interview_report, timestamps }
- ``interview_turns`` — { _id, interview_id, turn_number, question_text,
                          user_answer_text, retrieved_facts, correctness_score,
                          feedback, next_question, created_at }
- ``user_progress``   — { _id, user_id, xp, level, streak, last_practice_date,
                          gems, achievements[], skill_tree{}, league, weekly_xp,
                          weekly_start_date, total_interviews, updated_at }
"""

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGO_URI)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[settings.MONGO_DB]
    return _db


async def init_indexes() -> None:
    """Create indexes. Unique (interview_id, turn_number) makes turn writes idempotent."""
    db = get_db()
    await db.interview_turns.create_index(
        [("interview_id", 1), ("turn_number", 1)], unique=True
    )
    await db.interviews.create_index([("user_id", 1)])
    await db.user_progress.create_index([("user_id", 1)], unique=True)
    await db.user_progress.create_index([("weekly_xp", -1)])


def close_client() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        _client = None
        _db = None
