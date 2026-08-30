import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    
    # NVIDIA STS (Speech-to-Speech) Model Settings
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_STS_BASE_URL = os.getenv("NVIDIA_STS_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_STS_MODEL = os.getenv("NVIDIA_STS_MODEL", "nvidia/speech-to-speech")
    NVIDIA_VOICE_NAME = os.getenv("NVIDIA_VOICE_NAME", "en-US-Standard-A")
    NVIDIA_STS_SAMPLE_RATE = int(os.getenv("NVIDIA_STS_SAMPLE_RATE", "16000"))
    
    # RAG Settings
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma_db")

settings = Settings()
