"""TTS：mlx-audio 加载 Qwen3-TTS，文本合成语音并播放。"""
import numpy as np
import sounddevice as sd
from mlx_audio.tts.utils import load_model


class TTS:
    def __init__(self, model="mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit", voice="serena"):
        self.model = load_model(model)
        self.voice = voice

    def synthesize(self, text):
        results = list(self.model.generate(text=text, voice=self.voice))
        audio = np.concatenate([np.asarray(r.audio) for r in results])
        return audio, results[0].sample_rate

    def speak(self, text):
        audio, sr = self.synthesize(text)
        sd.play(audio, sr)
        sd.wait()
