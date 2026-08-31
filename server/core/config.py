import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Reasoning LLM (DeepSeek, OpenAI-compatible) ---
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

    # --- NVIDIA Speech-to-Speech (STS) ---
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_STS_BASE_URL = os.getenv("NVIDIA_STS_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_STS_MODEL = os.getenv("NVIDIA_STS_MODEL", "nvidia/speech-to-speech")
    NVIDIA_VOICE_NAME = os.getenv("NVIDIA_VOICE_NAME", "en-US-Standard-A")
    NVIDIA_STS_SAMPLE_RATE = int(os.getenv("NVIDIA_STS_SAMPLE_RATE", "16000"))

    # --- RAG vector store (Postgres + pgvector) ---
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://interview:interview@localhost:5432/interview"
    )
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

    # --- Application data (MongoDB) ---
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB = os.getenv("MONGO_DB", "interview")


settings = Settings()
