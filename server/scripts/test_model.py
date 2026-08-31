"""Smoke test for the NVIDIA Speech-to-Speech service.

Run from the ``server/`` directory:

    python -m scripts.test_model
    # or
    python scripts/test_model.py
"""

import asyncio
import os
import sys

# Make the server/ package root importable when run as a plain script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.nvidia_sts_service import NVIDIASTSService


async def test_nvidia_sts():
    print("Testing NVIDIA STS (Speech-to-Speech) service...")
    sts = NVIDIASTSService()

    res = await sts.process_speech_turn(
        text_prompt="I have built distributed systems with Kafka and PostgreSQL.",
        context="Candidate with 3 years backend engineering experience.",
    )

    print(f"Transcript: {res['transcript']}")
    print(f"Response:   {res['response_text']}")
    print(f"Audio bytes: {len(res['audio_bytes'])} bytes")
    print(f"Latency:    {res['latency_ms']} ms")
    print(f"Model:      {res['model']}")
    print("NVIDIA STS service test completed.")


if __name__ == "__main__":
    asyncio.run(test_nvidia_sts())
