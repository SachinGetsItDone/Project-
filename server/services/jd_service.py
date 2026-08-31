"""Job-description analysis.

Thin async wrapper over the LLM gateway so the endpoint and the interview-setup
flow share one code path. Kept as its own module so JD logic has a clear home
and can grow (e.g. caching, skill taxonomies) without touching the gateway.
"""

from services.llm_gateway import LLMGateway


class JDService:
    def __init__(self, llm: LLMGateway):
        self.llm = llm

    async def analyze(self, jd_text: str) -> dict:
        return await self.llm.analyze_jd(jd_text)
