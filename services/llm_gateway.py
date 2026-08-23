import os
from openai import AsyncOpenAI
import json

from core.config import settings

class LLMGateway:
    def __init__(self):
        # DeepSeek API uses OpenAI-compatible endpoints
        self.client = AsyncOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
        )
        self.primary_model = "deepseek-chat" # Fallback to v3 (deepseek-chat) if needed

    async def evaluate_and_generate_next(self, transcript: str, retrieved_facts: str, resume_context: str):
        """
        Evaluate user answer and generate the next interview question.
        Returns JSON formatted response containing: correctness_score, feedback, next_question
        """
        system_prompt = f"""
You are an expert technical interviewer conducting a mock interview.
Your task is to:
1. Evaluate the user's last answer based on the provided Domain Knowledge Facts.
2. Provide constructive feedback.
3. Ask the next relevant technical question.

---
Domain Knowledge Facts:
{retrieved_facts}

---
Candidate Context (Resume/JD):
{resume_context}
---

Respond strictly in JSON format matching this schema:
{{
  "correctness_score": <int 1-10>,
  "feedback": "<string: your constructive feedback>",
  "next_question": "<string: the next question to ask>"
}}
"""
        
        user_prompt = f"User's Answer: {transcript}"

        try:
            response = await self.client.chat.completions.create(
                model=self.primary_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            # Fallback behavior
            print(f"LLM generation failed: {e}")
            return {
                "correctness_score": 0,
                "feedback": "I had some trouble evaluating your last answer.",
                "next_question": "Could you elaborate more on your previous experience?"
            }
