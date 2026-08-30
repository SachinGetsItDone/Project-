import asyncio
from services.nvidia_sts_service import NVIDIASTSService

async def test_nvidia_sts():
    print("Testing NVIDIA STS (Speech-to-Speech) Model...")
    sts = NVIDIASTSService()
    
    # 1. Test speech generation with text prompt fallback
    res = await sts.process_speech_turn(
        text_prompt="I have built distributed systems with Kafka and PostgreSQL.",
        context="Candidate with 3 years backend engineering experience."
    )
    
    print(f"Transcript: {res['transcript']}")
    print(f"Response: {res['response_text']}")
    print(f"Audio bytes generated: {len(res['audio_bytes'])} bytes")
    print(f"Latency: {res['latency_ms']} ms")
    print(f"Model: {res['model']}")
    print("NVIDIA STS Model test completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_nvidia_sts())
