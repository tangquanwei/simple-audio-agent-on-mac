"""silero-vad 语音分段。

VADSegmenter：纯分段器，喂 16kHz float32 PCM，说完一段返回该段（供 WebSocket 等流式场景）。
MicVAD：基于 sounddevice 的麦克风封装，record_segment() 阻塞返回一段语音（供 CLI）。
"""
import queue
import time

import numpy as np
import sounddevice as sd
import torch
from silero_vad import load_silero_vad

SAMPLE_RATE = 16000
CHUNK = 512  # silero 在 16kHz 下要求 512 采样（32ms）


class VADSegmenter:
    """逐块喂 PCM，检测到「说话开始 → 静音超时」后返回一段完整语音。"""

    def __init__(self, threshold=0.5, silence_limit=0.8, max_segment=15.0, min_segment=0.3):
        self.model = load_silero_vad(onnx=True)
        self.threshold = threshold
        self.silence_limit = silence_limit
        self.max_segment = max_segment
        self.min_segment = min_segment
        self._pending = np.zeros(0, dtype=np.float32)  # 不足一个 CHUNK 的剩余
        self._reset()

    def _reset(self):
        self._triggered = False
        self._speech = []
        self._silence = 0.0
        self._start = None

    def feed(self, samples):
        """喂入任意长度的 16kHz float32 PCM；说完一段时返回 np.ndarray，否则 None。"""
        self._pending = np.concatenate([self._pending, samples])
        while len(self._pending) >= CHUNK:
            chunk, self._pending = self._pending[:CHUNK], self._pending[CHUNK:]
            segment = self._feed_chunk(chunk)
            if segment is not None:
                return segment
        return None

    def _feed_chunk(self, chunk):
        prob = float(self.model(torch.from_numpy(chunk), SAMPLE_RATE))
        speaking = prob > self.threshold
        if not self._triggered:
            if speaking:
                self._triggered = True
                self._speech = [chunk]
                self._silence = 0.0
                self._start = time.perf_counter()
            return None
        self._speech.append(chunk)
        elapsed = time.perf_counter() - self._start
        if speaking:
            self._silence = 0.0
        else:
            self._silence += CHUNK / SAMPLE_RATE
        if self._silence >= self.silence_limit or elapsed >= self.max_segment:
            audio = np.concatenate(self._speech)
            self._reset()
            if elapsed >= self.min_segment:
                return audio
        return None


class MicVAD:
    def __init__(self, **vad_kwargs):
        self.segmenter = VADSegmenter(**vad_kwargs)
        self._queue = queue.Queue()
        self._stream = None

    def _callback(self, indata, frames, time_info, status):
        self._queue.put(indata[:, 0].copy())

    def start(self):
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=1, dtype="float32",
            blocksize=CHUNK, callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *exc):
        self.stop()

    def record_segment(self):
        """阻塞直到录到一段完整语音，返回 (samples, sample_rate)。"""
        while True:
            segment = self.segmenter.feed(self._queue.get())
            if segment is not None:
                return segment, SAMPLE_RATE
