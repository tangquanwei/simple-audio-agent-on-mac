"""STT：mlx-whisper 转写 16kHz float32 PCM。"""
import mlx_whisper


class STT:
    def __init__(self, model="mlx-community/whisper-large-v3-turbo", language="zh"):
        self.model = model
        self.language = language

    def transcribe(self, audio):
        result = mlx_whisper.transcribe(audio, path_or_hf_repo=self.model, language=self.language)
        return result["text"].strip()
