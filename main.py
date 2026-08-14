#!/usr/bin/env python
"""本地 speech-to-speech 对话：麦克风 → VAD → STT → LLM → TTS → 播放，循环运行。

用法：
    python main.py
    python main.py --stt-model mlx-community/whisper-small-mlx --language zh
Ctrl+C 退出。
"""
import argparse
import time

from saam.llm import LLM
from saam.stt import STT
from saam.tts import TTS
from saam.vad import MicVAD


def timed(fn):
    t0 = time.perf_counter()
    out = fn()
    return out, time.perf_counter() - t0


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stt-model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--llm-model", default="mlx-community/Qwen3-0.6B-4bit")
    parser.add_argument("--tts-model", default="mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit")
    parser.add_argument("--voice", default="serena")
    parser.add_argument("--language", default="zh")
    args = parser.parse_args()

    print("加载模型中（首次运行会下载）...")
    stt, dt = timed(lambda: STT(args.stt_model, args.language))
    print(f"  STT 就绪 {dt:.1f}s")
    llm, dt = timed(lambda: LLM(args.llm_model))
    print(f"  LLM 就绪 {dt:.1f}s")
    tts, dt = timed(lambda: TTS(args.tts_model, args.voice))
    print(f"  TTS 就绪 {dt:.1f}s")

    print("\n对话开始，请说话（Ctrl+C 退出）\n")
    try:
        with MicVAD() as mic:
            while True:
                print("聆听中...", end="\r", flush=True)
                audio, sr = mic.record_segment()
                print(f"录音 {len(audio) / sr:.1f}s，转写中...   ")

                text, dt = timed(lambda: stt.transcribe(audio))
                if not text:
                    print("（未识别到语音）")
                    continue
                print(f"你: {text}  ({dt:.1f}s)")

                print("助手: ", end="", flush=True)
                reply, dt = timed(lambda: llm.chat(text, on_token=lambda t: print(t, end="", flush=True)))
                print(f"  ({dt:.1f}s)")

                _, dt = timed(lambda: tts.speak(reply))
                print(f"播放完毕 ({dt:.1f}s)\n")
    except KeyboardInterrupt:
        print("\n再见！")


if __name__ == "__main__":
    main()
