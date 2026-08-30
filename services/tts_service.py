"""
[DEPRECATED] Standalone TTS Service has been completely removed.
The project now uses NVIDIA Speech-to-Speech (STS) model via services.nvidia_sts_service.NVIDIASTSService.
"""
from services.nvidia_sts_service import NVIDIASTSService as TTSService
