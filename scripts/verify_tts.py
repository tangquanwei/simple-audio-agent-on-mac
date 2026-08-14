"""验证 TTS：Qwen3-TTS 合成一段中文语音，保存 out.wav 并播放。"""
import argparse
import subprocess
import time

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

DEFAULT_MODEL = "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--text", default="你好，我是本地运行的语音助手，今天天气不错。")
    parser.add_argument("--voice", default="serena")
    parser.add_argument("--out", default="out.wav")
    parser.add_argument("--no-play", action="store_true")
    args = parser.parse_args()

    t0 = time.perf_counter()
    model = load_model(args.model)
    print(f"[tts] 模型加载 {time.perf_counter() - t0:.1f}s")

    t0 = time.perf_counter()
    results = list(model.generate(text=args.text, voice=args.voice, verbose=True))
    audio = np.concatenate([np.asarray(r.audio) for r in results])
    sr = results[0].sample_rate
    print(f"[tts] 合成 {time.perf_counter() - t0:.1f}s, 音频 {len(audio) / sr:.1f}s @ {sr}Hz")

    sf.write(args.out, audio, sr)
    print(f"[tts] 已保存 {args.out}")

    if not args.no_play:
        subprocess.run(["afplay", args.out], check=True)


if __name__ == "__main__":
    main()
