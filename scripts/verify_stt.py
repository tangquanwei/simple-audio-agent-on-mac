"""验证 STT：用 mlx-whisper 转写一段音频（默认用 verify_tts.py 生成的 out.wav）。"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from saam.stt import STT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--audio", default="out.wav")
    parser.add_argument("--language", default="zh")
    args = parser.parse_args()

    stt = STT(args.model, args.language)
    t0 = time.perf_counter()
    text = stt.transcribe(args.audio)
    print(f"[stt] 转写 {time.perf_counter() - t0:.1f}s")
    print(f"[stt] 文本: {text}")


if __name__ == "__main__":
    main()
