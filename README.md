<div align="center">

# 🎙️ saam — Simple Audio Agent on Mac

**saam = Simple Audio Agent on Mac: a fully local, MLX-powered speech-to-speech pipeline that turns "you speak" into "it answers" on Apple Silicon**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MLX](https://img.shields.io/badge/MLX-Apple%20Silicon-000000?logo=apple&logoColor=white)](https://ml-explore.github.io/mlx/build/html/index.html)
[![STT](https://img.shields.io/badge/STT-Whisper%20large--v3--turbo-74aa9c)](https://huggingface.co/mlx-community/whisper-large-v3-turbo)
[![LLM](https://img.shields.io/badge/LLM-Qwen3--0.6B--4bit-6E4AFF)](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit)
[![TTS](https://img.shields.io/badge/TTS-Qwen3--TTS%200.6B-FF6F61)](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit)
[![CI](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml/badge.svg)](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🗣️ Speak → 🤖 Think → 🔊 Answer · **No cloud, no API keys, no subscriptions**

English · [中文](README.zh-CN.md) · [日本語](README.ja.md) · [한국어](README.ko.md)

[Quick Start](#-quick-start) · [Real-time WebUI](#-real-time-webui) · [CLI](#-cli-conversation) · [Project Layout](#-project-layout) · [Roadmap](#-roadmap)

<img src="images/webui.png" alt="saam WebUI — real-time voice conversation" width="720">

</div>

---

## ✨ Features

- 🔒 **Fully local**: STT, LLM, and TTS all run on your Mac — audio never leaves the machine
- ⚡ **MLX end to end**: all three models run natively on MLX, with sub-second-class responses on unified memory
- 👂 **Always listening**: silero-vad detects when you start and stop talking — **no push-to-talk**, just pause and it answers
- 🌐 **Two interfaces**: a minimal real-time WebUI (talk right in the browser) + a terminal CLI, sharing one pipeline
- 🧩 **Modular**: VAD / STT / LLM / TTS are independent modules — swap any of them out

## 🧠 How It Works

```
🎤 Microphone
   │
   ▼
┌─────────────┐   16kHz PCM, auto-segment after 0.8s of silence
│  silero-vad │
└─────────────┘
   │  one complete utterance
   ▼
┌─────────────────────┐
│  Whisper large-v3   │  📝 "How's the weather today?"
│      (turbo)        │
└─────────────────────┘
   │  text
   ▼
┌─────────────────────┐
│    Qwen3-0.6B       │  💭 "It's sunny — perfect for a walk."
│  (4bit, streaming)  │
└─────────────────────┘
   │  reply text
   ▼
┌─────────────────────┐
│     Qwen3-TTS       │  🔊 natural-sounding speech
│   (12Hz, 8bit)      │
└─────────────────────┘
   │
   ▼
🔊 Speaker / browser playback
```

Measured latency (M5, short sentence): **STT ~1.4s · LLM ~1.0s · TTS ~2.6s**

## 🚀 Quick Start

> [!IMPORTANT]
> You need an Apple Silicon Mac and Python 3.12 (newer system versions like 3.14 are too new for MLX). [uv](https://docs.astral.sh/uv/) is recommended.

```bash
# 1. Create the environment
uv venv --python 3.12 .venv

# 2. Install dependencies
uv pip install --python .venv/bin/python -r requirements.txt

# 3. Launch the real-time WebUI (first run downloads ~3GB of models)
.venv/bin/python webui.py
```

Open <http://127.0.0.1:7860>, click **"开始对话" (Start Conversation)**, and just talk 🎉

> [!NOTE]
> macOS will ask for microphone permission on first use — allow it for your terminal / browser.

## 🌐 Real-time WebUI
![alt text](images/README/2026-08-14T01:53:44.187Z.png)
Click once, and VAD takes care of the rest:

- 🟢 **Listening** — just speak; the browser streams 16kHz PCM over WebSocket
- 🟡 **Processing** — pause for ~0.8s and the server cuts the segment and starts the pipeline
- 🔊 **Speaking** — the reply appears as a chat bubble and plays automatically; uplink pauses during playback so the agent never hears itself

Multiple browser connections are supported; inference requests are queued.

## 💻 CLI Conversation

```bash
.venv/bin/python main.py
```

Speak → transcribe → print the reply → play the voice, in a loop. `Ctrl+C` to quit.

Or install the entry points once — `uv pip install --python .venv/bin/python -e .` — then just run `saam` (CLI) or `saam-web` (WebUI).

<details>
<summary>⚙️ Options (shared by webui.py and main.py)</summary>

| Flag | Default | Description |
| --- | --- | --- |
| `--stt-model` | `mlx-community/whisper-large-v3-turbo` | Speech recognition model |
| `--llm-model` | `mlx-community/Qwen3-0.6B-4bit` | Chat model |
| `--tts-model` | `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit` | Speech synthesis model |
| `--voice` | `serena` | TTS voice |
| `--language` | `zh` | Recognition language |
| `--host` / `--port` | `127.0.0.1` / `7860` | WebUI listen address |

</details>

## 🧪 Stage-by-stage Verification

Each stage has its own script, so problems are easy to isolate:

```bash
.venv/bin/python scripts/verify_tts.py   # TTS: synthesize a sentence → out.wav and play it
.venv/bin/python scripts/verify_stt.py   # STT: transcribe out.wav → print the text
.venv/bin/python scripts/verify_llm.py   # LLM: run one round of conversation
```

## 📁 Project Layout

```
main.py              # CLI entry: VAD recording → STT → LLM → TTS → playback, looping
webui.py             # Real-time WebUI: FastAPI + WebSocket, same pipeline
saam/
  vad.py             # VADSegmenter (streaming segmentation) + MicVAD (microphone wrapper)
  stt.py             # mlx-whisper wrapper
  llm.py             # mlx-lm wrapper: multi-turn chat, streaming output
  tts.py             # mlx-audio Qwen3-TTS wrapper
scripts/             # Standalone verification scripts for each stage
requirements.txt     # Pinned dependencies (uv pip freeze)
```

## 🛠️ Tech Stack

| Stage | Solution | Model |
| --- | --- | --- |
| VAD | [silero-vad](https://github.com/snakers4/silero-vad) (ONNX, onnxruntime) | built-in |
| STT | [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) | `whisper-large-v3-turbo` |
| LLM | [mlx-lm](https://github.com/ml-explore/mlx-lm) | `Qwen3-0.6B-4bit` |
| TTS | [mlx-audio](https://github.com/Blaizzy/mlx-audio) | `Qwen3-TTS-12Hz-0.6B-Base-8bit` |

> [!TIP]
> Two real-world pitfalls already solved here: Qwen3 emits its `<think>` reasoning by default (the TTS would read the thinking out loud) — disabled via `enable_thinking=False`. And lightning-whisper-mlx 0.0.10 is incompatible with mlx 0.32, so STT uses the officially maintained mlx-whisper instead.

Inspired by [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech).

## ❓ FAQ

**Which languages are supported?**
Recognition is multilingual via Whisper — pass `--language en`, `ja`, `ko`, etc. (default `zh`). The Qwen3 LLM and Qwen3-TTS handle Chinese and English best.

**The agent reads its "thinking" out loud.**
Qwen3 emits `<think>` reasoning by default; saam disables it with `enable_thinking=False`. If you swap in another reasoning model, strip its thinking tags before TTS.

**The first run is very slow.**
That's the one-time model download (~3GB); afterwards startup takes seconds. If HuggingFace is slow where you are, try `HF_ENDPOINT=https://hf-mirror.com`.

**The microphone doesn't respond.**
Grant access in System Settings → Privacy & Security → Microphone for your terminal and browser. In the browser, mic capture requires `localhost` / `127.0.0.1` (or HTTPS).

**"Address already in use" on port 7860?**
Pass `--port 7861`, or find the stale process with `lsof -nP -iTCP:7860 -sTCP:LISTEN`.

## 🗺️ Roadmap

- [x] Environment: uv + Python 3.12 venv
- [x] VAD: real-time speech segmentation with silero-vad
- [x] Stage-by-stage verification of STT / LLM / TTS
- [x] Full loop: record → STT → LLM → TTS → playback
- [x] Real-time WebUI (WebSocket streaming + auto-segmentation)
- [ ] Barge-in: detect the user interrupting during playback ([#1](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/1))
- [ ] Streaming TTS (`stream=True`) for lower time-to-first-audio ([#2](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/2))
- [ ] CustomVoice model: more voices and emotion instructions ([#3](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/3))

---

<div align="center">

🍎 Made with MLX on Apple Silicon · Every word you say stays on your own machine

</div>
