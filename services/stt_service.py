import torch
from transformers import pipeline
import numpy as np

class STTService:
    def __init__(self, model_id: str = "openai/whisper-small"):
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.pipe = pipeline(
            "automatic-speech-recognition",
            model=model_id,
            chunk_length_s=30,
            device=self.device,
        )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribe an audio numpy array.
        Audio data should be a 1D numpy array of float32, sampled at 16000 Hz.
        """
        # The transformers pipeline can take a dictionary with raw audio
        input_data = {"array": audio_data, "sampling_rate": sample_rate}
        
        # We can also get timestamps, but for the basic flow we just need text.
        prediction = self.pipe(input_data, batch_size=8)
        return prediction["text"].strip()
