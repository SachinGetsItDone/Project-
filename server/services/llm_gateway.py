"""DeepSeek-backed reasoning gateway.

Handles four LLM tasks, each with a graceful local fallback when no API key is
configured so the app stays usable offline:

1. ``evaluate_and_generate_next`` — score an answer + author the next question.
2. ``analyze_jd``                 — turn a job description into structured skills.
3. ``generate_opening_question``  — the first interview question.
4. ``generate_report``            — the structured post-interview report.
"""

import json
from typing import List, Optional

from openai import AsyncOpenAI

from core.config import settings


class LLMGateway:
    def __init__(self):
        # DeepSeek exposes OpenAI-compatible endpoints.
        api_key = settings.DEEPSEEK_API_KEY or "dummy_deepseek_key"
        self.client = AsyncOpenAI(api_key=api_key, base_url=settings.DEEPSEEK_BASE_URL)
        self.primary_model = "deepseek-chat"

    async def _chat_json(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> dict:
        """Call DeepSeek in JSON mode and parse the result."""
        response = await self.client.chat.completions.create(
            model=self.primary_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return json.loads(response.choices[0].message.content)

    # ------------------------------------------------------------------ #
    # 1. Evaluate the answer and generate the next question
    # ------------------------------------------------------------------ #
    async def evaluate_and_generate_next(
        self, transcript: str, retrieved_facts: str, resume_context: str
    ) -> dict:
        if not settings.DEEPSEEK_API_KEY:
            return {
                "correctness_score": 8,
                "feedback": "Strong explanation of the architectural tradeoffs and concurrency controls.",
                "next_question": "How would you handle database partitioning and high availability during failovers?",
            }

        system_prompt = f"""
You are an expert technical interviewer conducting a mock interview.
Your task is to:
1. Evaluate the candidate's last answer using the Domain Knowledge Facts.
2. Provide constructive feedback.
3. Ask the next relevant technical question.

---
Domain Knowledge Facts:
{retrieved_facts}

---
Candidate Context (Resume/JD):
{resume_context}
---

Respond strictly in JSON matching this schema:
{{
  "correctness_score": <int 1-10>,
  "feedback": "<string: constructive feedback>",
  "next_question": "<string: the next question to ask>"
}}
"""
        try:
            return await self._chat_json(system_prompt, f"Candidate's answer: {transcript}")
        except Exception as e:
            print(f"LLM evaluation failed: {e}")
            return {
                "correctness_score": 7,
                "feedback": "I had trouble reaching the evaluation model, but noted your key points.",
                "next_question": "Could you elaborate more on your previous experience?",
            }

    # ------------------------------------------------------------------ #
    # 2. Analyze a job description
    # ------------------------------------------------------------------ #
    async def analyze_jd(self, jd_text: str) -> dict:
        if not jd_text or not jd_text.strip():
            return {"role": "", "key_skills": [], "focus_areas": []}

        if not settings.DEEPSEEK_API_KEY:
            return self._fallback_jd_analysis(jd_text)

        system_prompt = """
You analyze job descriptions for a technical interview platform.
Extract the target role, the key technical skills, and the focus areas an
interviewer should probe. Respond strictly in JSON matching this schema:
{
  "role": "<string: the job title / role>",
  "key_skills": ["<skill>", ...],
  "focus_areas": ["<topic an interviewer should test>", ...]
}
"""
        try:
            data = await self._chat_json(system_prompt, f"Job description:\n{jd_text}")
            # Normalize shapes defensively.
            return {
                "role": data.get("role", ""),
                "key_skills": list(data.get("key_skills", []))[:15],
                "focus_areas": list(data.get("focus_areas", []))[:10],
            }
        except Exception as e:
            print(f"JD analysis failed: {e}")
            return self._fallback_jd_analysis(jd_text)

    @staticmethod
    def _fallback_jd_analysis(jd_text: str) -> dict:
        known = [
            "python", "java", "javascript", "typescript", "react", "node",
            "sql", "postgresql", "mongodb", "redis", "kafka", "docker",
            "kubernetes", "aws", "system design", "data structures",
            "algorithms", "microservices", "rest", "api", "distributed systems",
        ]
        low = jd_text.lower()
        found = [s for s in known if s in low]
        return {
            "role": "",
            "key_skills": found[:15],
            "focus_areas": (found[:5] or ["data structures", "system design", "behavioral"]),
        }

    # ------------------------------------------------------------------ #
    # 3. Opening question
    # ------------------------------------------------------------------ #
    async def generate_opening_question(
        self, role: str, jd_analysis: Optional[dict], resume_context: str
    ) -> str:
        focus = ""
        if jd_analysis and jd_analysis.get("focus_areas"):
            focus = jd_analysis["focus_areas"][0]

        if not settings.DEEPSEEK_API_KEY:
            base = role or "software engineering"
            if focus:
                return f"To start, tell me about your experience with {focus} in a {base} context."
            return f"To start, tell me about a challenging {base} project you worked on and your specific contribution."

        system_prompt = """
You are a technical interviewer. Produce a single, warm opening interview
question tailored to the role and context. Respond strictly in JSON:
{ "question": "<string>" }
"""
        user_prompt = f"Role: {role}\nFocus area: {focus}\nCandidate context: {resume_context[:1500]}"
        try:
            data = await self._chat_json(system_prompt, user_prompt, temperature=0.5)
            return data.get("question") or f"To start, tell me about a challenging {role or 'engineering'} project you worked on."
        except Exception as e:
            print(f"Opening-question generation failed: {e}")
            return f"To start, tell me about a challenging {role or 'engineering'} project you worked on."

    # ------------------------------------------------------------------ #
    # 4. Post-interview report
    # ------------------------------------------------------------------ #
    async def generate_report(
        self, turns: List[dict], resume_context: str, jd_analysis: Optional[dict]
    ) -> dict:
        if not settings.DEEPSEEK_API_KEY:
            return self._fallback_report(turns)

        # Compact transcript of the interview for the model.
        lines = []
        for t in turns:
            lines.append(
                f"Q{t.get('turn_number')}: {t.get('question_text', '')}\n"
                f"A: {t.get('user_answer_text', '')}\n"
                f"score={t.get('correctness_score')} feedback={t.get('feedback', '')}"
            )
        transcript = "\n\n".join(lines) if lines else "(no answered turns)"

        system_prompt = """
You are a senior interviewer writing a post-interview report. Summarize the
candidate's performance. Respond strictly in JSON matching this schema:
{
  "overall_score": <int 1-10>,
  "competencies": [{ "name": "<string>", "score": <int 1-10>, "comment": "<string>" }],
  "strengths": ["<string>", ...],
  "gaps": ["<string>", ...],
  "summary": "<string>"
}
"""
        focus = ", ".join((jd_analysis or {}).get("focus_areas", [])) or "general technical"
        user_prompt = f"Focus areas: {focus}\nCandidate context: {resume_context[:1000]}\n\nInterview:\n{transcript}"
        try:
            return await self._chat_json(system_prompt, user_prompt, temperature=0.4)
        except Exception as e:
            print(f"Report generation failed: {e}")
            return self._fallback_report(turns)

    @staticmethod
    def _fallback_report(turns: List[dict]) -> dict:
        scores = [
            t.get("correctness_score")
            for t in turns
            if isinstance(t.get("correctness_score"), (int, float))
        ]
        avg = round(sum(scores) / len(scores), 1) if scores else 0
        return {
            "overall_score": avg,
            "competencies": [
                {"name": "Technical depth", "score": avg, "comment": "Derived from per-answer scores."}
            ],
            "strengths": ["Completed the interview turns."] if turns else [],
            "gaps": ["Connect an LLM API key for a detailed qualitative report."],
            "summary": f"Answered {len(turns)} question(s) with an average score of {avg}/10. "
            "This is a locally-computed fallback report; set DEEPSEEK_API_KEY for a full narrative.",
        }
