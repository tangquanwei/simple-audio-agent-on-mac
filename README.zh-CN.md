<div align="center">

# 🎙️ saam — Simple Audio Agent on Mac

**saam = Simple Audio Agent on Mac：在 Apple Silicon 上，用一条 MLX 全链路流水线，把「你说」变成「它答」**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MLX](https://img.shields.io/badge/MLX-Apple%20Silicon-000000?logo=apple&logoColor=white)](https://ml-explore.github.io/mlx/build/html/index.html)
[![STT](https://img.shields.io/badge/STT-Whisper%20large--v3--turbo-74aa9c)](https://huggingface.co/mlx-community/whisper-large-v3-turbo)
[![LLM](https://img.shields.io/badge/LLM-Qwen3--0.6B--4bit-6E4AFF)](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit)
[![TTS](https://img.shields.io/badge/TTS-Qwen3--TTS%200.6B-FF6F61)](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit)
[![CI](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml/badge.svg)](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🗣️ 说话 → 🤖 思考 → 🔊 回答 · **零云端、零 API Key、零订阅**

[English](README.md) · 中文 · [日本語](README.ja.md) · [한국어](README.ko.md)

[快速开始](#-快速开始) · [实时 WebUI](#-实时-webui) · [命令行对话](#-命令行对话) · [项目结构](#-项目结构) · [路线图](#-路线图)

<img src="images/webui.png" alt="saam WebUI — 实时语音对话界面" width="720">

</div>

---

## ✨ 特性

- 🔒 **完全本地**：STT、LLM、TTS 全部跑在你的 Mac 上，音频不出本机
- ⚡ **MLX 全链路加速**：三个模型均为 MLX 原生推理，统一内存架构下秒级响应
- 👂 **实时聆听**：silero-vad 自动检测说话开始与结束，**不用按任何键**，停顿即回答
- 🌐 **双模式**：极简 WebUI（浏览器直接对话）+ 终端 CLI，同一套流水线
- 🧩 **模块化**：VAD / STT / LLM / TTS 四个独立模块，想换哪个换哪个

## 🧠 工作原理

```
🎤 麦克风
   │
   ▼
┌─────────────┐   16kHz PCM，静音 0.8s 自动切段
│  silero-vad │
└─────────────┘
   │  一段完整语音
   ▼
┌─────────────────────┐
│  Whisper large-v3   │  📝 "今天天气怎么样？"
│      (turbo)        │
└─────────────────────┘
   │  文本
   ▼
┌─────────────────────┐
│    Qwen3-0.6B       │  💭 "今天晴空万里，适合出门走走。"
│   (4bit, 流式)      │
└─────────────────────┘
   │  回复文本
   ▼
┌─────────────────────┐
│     Qwen3-TTS       │  🔊 自然中文语音
│   (12Hz, 8bit)      │
└─────────────────────┘
   │
   ▼
🔊 扬声器 / 浏览器播放
```

实测延迟（M5，短句）：**STT ~1.4s · LLM ~1.0s · TTS ~2.6s**

## 🚀 快速开始

> [!IMPORTANT]
> 需要 Apple Silicon Mac 与 Python 3.12（更高的系统版本如 3.14 对 MLX 来说太新）。推荐使用 [uv](https://docs.astral.sh/uv/)。

```bash
# 1. 创建环境
uv venv --python 3.12 .venv

# 2. 安装依赖
uv pip install --python .venv/bin/python -r requirements.txt

# 3. 启动实时 WebUI（首次运行自动下载模型，约 3GB）
.venv/bin/python webui.py
```

打开 <http://127.0.0.1:7860>，点 **「开始对话」**，然后直接说话 🎉

> [!NOTE]
> 首次使用麦克风时 macOS 会请求权限，请允许终端 / 浏览器访问。

## 🌐 实时 WebUI

点一次「开始对话」，剩下的交给 VAD：

- 🟢 **聆听中** — 直接说话，浏览器通过 WebSocket 持续推送 16kHz PCM
- 🟡 **识别与生成中** — 你停顿约 0.8 秒，服务端自动切段并开始处理
- 🔊 **播放回复中** — 页面显示对话气泡并自动播放语音；播放期间暂停上行，助手不会听到自己的声音

支持多浏览器连接，推理请求自动排队。

## 💻 命令行对话

```bash
.venv/bin/python main.py
```

说话 → 自动转写 → 打印回复 → 播放语音，循环对话，`Ctrl+C` 退出。

也可以先安装命令入口 —— `uv pip install --python .venv/bin/python -e .` —— 之后直接运行 `saam`（CLI）或 `saam-web`（WebUI）。

<details>
<summary>⚙️ 可选参数（webui.py 与 main.py 通用）</summary>

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `--stt-model` | `mlx-community/whisper-large-v3-turbo` | 语音识别模型 |
| `--llm-model` | `mlx-community/Qwen3-0.6B-4bit` | 对话模型 |
| `--tts-model` | `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit` | 语音合成模型 |
| `--voice` | `serena` | TTS 音色 |
| `--language` | `zh` | 识别语言 |
| `--host` / `--port` | `127.0.0.1` / `7860` | WebUI 监听地址 |

</details>

## 🧪 分步验证

每个环节都有独立脚本，出问题好定位：

```bash
.venv/bin/python scripts/verify_tts.py   # TTS：合成一句话 → out.wav 并播放
.venv/bin/python scripts/verify_stt.py   # STT：转写 out.wav → 打印文本
.venv/bin/python scripts/verify_llm.py   # LLM：跑一轮中文对话
```

## 📁 项目结构

```
main.py              # CLI 主程序：VAD 录音 → STT → LLM → TTS → 播放，循环对话
webui.py             # 实时 WebUI：FastAPI + WebSocket，同一套流水线
saam/
  vad.py             # VADSegmenter（流式分段）+ MicVAD（麦克风封装）
  stt.py             # mlx-whisper 封装
  llm.py             # mlx-lm 封装：多轮对话、流式输出
  tts.py             # mlx-audio Qwen3-TTS 封装
scripts/             # 各环节独立验证脚本
requirements.txt     # 锁定依赖（uv pip freeze）
```

## 🛠️ 技术栈

| 环节 | 方案 | 模型 |
| --- | --- | --- |
| VAD | [silero-vad](https://github.com/snakers4/silero-vad)（ONNX，onnxruntime 推理） | 内置 |
| STT | [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) | `whisper-large-v3-turbo` |
| LLM | [mlx-lm](https://github.com/ml-explore/mlx-lm) | `Qwen3-0.6B-4bit` |
| TTS | [mlx-audio](https://github.com/Blaizzy/mlx-audio) | `Qwen3-TTS-12Hz-0.6B-Base-8bit` |

> [!TIP]
> 两个实践中的坑，已在本项目中解决：Qwen3 默认输出 `<think>` 推理过程（TTS 会把思考内容念出来），已通过 `enable_thinking=False` 关闭；lightning-whisper-mlx 0.0.10 与 mlx 0.32 不兼容，故 STT 采用官方维护的 mlx-whisper。

参考项目：[huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech)

## ❓ 常见问题

**支持哪些语言？**
识别端 Whisper 是多语言的 —— 用 `--language en`、`ja`、`ko` 等切换（默认 `zh`）。LLM（Qwen3）和 Qwen3-TTS 对中英文支持最好。

**助手会把「思考过程」念出来。**
Qwen3 默认输出 `<think>` 推理内容，saam 已通过 `enable_thinking=False` 关闭。如果自行更换其他推理模型，记得在送 TTS 前剥掉思考标签。

**第一次运行很慢。**
那是模型的一次性下载（约 3GB），之后启动只需几秒。HuggingFace 下载慢可以设 `HF_ENDPOINT=https://hf-mirror.com`。

**麦克风没反应。**
在 系统设置 → 隐私与安全性 → 麦克风 中允许终端和浏览器访问。浏览器录音要求用 `localhost` / `127.0.0.1`（或 HTTPS）访问页面。

**7860 端口被占用？**
换端口 `--port 7861`，或用 `lsof -nP -iTCP:7860 -sTCP:LISTEN` 找到残留进程。

## 🗺️ 路线图

- [x] 环境：uv + Python 3.12 venv
- [x] VAD：silero-vad 实时语音分段
- [x] STT / LLM / TTS 分步验证
- [x] 串联：录音 → STT → LLM → TTS → 播放，循环对话
- [x] 实时 WebUI（WebSocket 流式 + 自动切段）
- [ ] barge-in：播放回复时检测用户打断（[#1](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/1)）
- [ ] TTS 边生成边播放（`stream=True`），降低首音延迟（[#2](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/2)）
- [ ] CustomVoice 模型：更多音色与情感指令（[#3](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/3)）

---

<div align="center">

🍎 Made with MLX on Apple Silicon · 说的每句话，都留在你自己的机器上

</div>
