<div align="center">

# 🎙️ saam — Simple Audio Agent on Mac

**saam = Simple Audio Agent on Mac：Apple Silicon 上で動く、完全ローカルの MLX フルパイプライン。「話す」がそのまま「答え」になる**

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![MLX](https://img.shields.io/badge/MLX-Apple%20Silicon-000000?logo=apple&logoColor=white)](https://ml-explore.github.io/mlx/build/html/index.html)
[![STT](https://img.shields.io/badge/STT-Whisper%20large--v3--turbo-74aa9c)](https://huggingface.co/mlx-community/whisper-large-v3-turbo)
[![LLM](https://img.shields.io/badge/LLM-Qwen3--0.6B--4bit-6E4AFF)](https://huggingface.co/mlx-community/Qwen3-0.6B-4bit)
[![TTS](https://img.shields.io/badge/TTS-Qwen3--TTS%200.6B-FF6F61)](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit)
[![CI](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml/badge.svg)](https://github.com/tangquanwei/simple-audio-agent-on-mac/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

🗣️ 話す → 🤖 考える → 🔊 答える · **クラウド不要、API キー不要、サブスク不要**

[English](README.md) · [中文](README.zh-CN.md) · 日本語 · [한국어](README.ko.md)

[クイックスタート](#-クイックスタート) · [リアルタイム WebUI](#-リアルタイム-webui) · [CLI](#-cli-会話) · [プロジェクト構成](#-プロジェクト構成) · [ロードマップ](#-ロードマップ)

<img src="images/webui.png" alt="saam WebUI — リアルタイム音声会話" width="720">

</div>

---

## ✨ 特徴

- 🔒 **完全ローカル**：STT・LLM・TTS がすべて Mac 上で動作。音声は外部に出ません
- ⚡ **MLX フルパイプライン**：3 つのモデルすべて MLX ネイティブ推論。ユニファイドメモリで秒級レスポンス
- 👂 **リアルタイムリスニング**：silero-vad が発話の開始と終了を自動検出。**ボタン操作不要**、間を置くだけで応答
- 🌐 **2 つのインターフェース**：ミニマルなリアルタイム WebUI（ブラウザで直接会話）＋ ターミナル CLI。パイプラインは共通
- 🧩 **モジュラー設計**：VAD / STT / LLM / TTS の 4 つの独立モジュール。差し替え自由

## 🧠 仕組み

```
🎤 マイク
   │
   ▼
┌─────────────┐   16kHz PCM、0.8 秒の無音で自動セグメント
│  silero-vad │
└─────────────┘
   │  ひと続きの発話
   ▼
┌─────────────────────┐
│  Whisper large-v3   │  📝 「今日の天気はどう？」
│      (turbo)        │
└─────────────────────┘
   │  テキスト
   ▼
┌─────────────────────┐
│    Qwen3-0.6B       │  💭 「晴れですね。散歩にぴったりですよ」
│ (4bit, ストリーミング)│
└─────────────────────┘
   │  応答テキスト
   ▼
┌─────────────────────┐
│     Qwen3-TTS       │  🔊 自然な音声
│   (12Hz, 8bit)      │
└─────────────────────┘
   │
   ▼
🔊 スピーカー / ブラウザ再生
```

実測レイテンシ（M5、短い文）：**STT ~1.4s · LLM ~1.0s · TTS ~2.6s**

## 🚀 クイックスタート

> [!IMPORTANT]
> Apple Silicon Mac と Python 3.12 が必要です（3.14 などの新しいシステム Python は MLX には新しすぎます）。[uv](https://docs.astral.sh/uv/) の使用を推奨します。

```bash
# 1. 環境を作成
uv venv --python 3.12 .venv

# 2. 依存関係をインストール
uv pip install --python .venv/bin/python -r requirements.txt

# 3. リアルタイム WebUI を起動（初回は約 3GB のモデルを自動ダウンロード）
.venv/bin/python webui.py
```

<http://127.0.0.1:7860> を開いて **「开始对话」（会話を開始）** をクリックし、そのまま話すだけ 🎉

> [!NOTE]
> 初回使用時に macOS がマイクへのアクセス許可を求めます。ターミナル / ブラウザへのアクセスを許可してください。

## 🌐 リアルタイム WebUI

一度クリックすれば、あとは VAD がすべて処理します：

- 🟢 **リスニング中** — そのまま話してください。ブラウザが WebSocket で 16kHz PCM を継続的に送信
- 🟡 **認識・生成中** — 約 0.8 秒間を置くと、サーバーがセグメントを切ってパイプラインを開始
- 🔊 **応答再生中** — 応答がチャットバブルに表示され自動再生。再生中はアップリンクを一時停止するので、エージェントが自分の声を聞くことはありません

複数ブラウザ接続に対応。推論リクエストは自動的にキューイングされます。

## 💻 CLI 会話

```bash
.venv/bin/python main.py
```

話す → 文字起こし → 応答を表示 → 音声再生、のループ。`Ctrl+C` で終了。

コマンドとしてインストールもできます —— `uv pip install --python .venv/bin/python -e .` —— 以降は `saam`（CLI）/ `saam-web`（WebUI）で起動できます。

<details>
<summary>⚙️ オプション（webui.py と main.py 共通）</summary>

| フラグ | デフォルト | 説明 |
| --- | --- | --- |
| `--stt-model` | `mlx-community/whisper-large-v3-turbo` | 音声認識モデル |
| `--llm-model` | `mlx-community/Qwen3-0.6B-4bit` | 会話モデル |
| `--tts-model` | `mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit` | 音声合成モデル |
| `--voice` | `serena` | TTS の声 |
| `--language` | `zh` | 認識言語 |
| `--host` / `--port` | `127.0.0.1` / `7860` | WebUI の待受アドレス |

</details>

## 🧪 ステップごとの検証

各ステージに独立したスクリプトがあるので、問題の切り分けが簡単です：

```bash
.venv/bin/python scripts/verify_tts.py   # TTS：文を合成 → out.wav に保存して再生
.venv/bin/python scripts/verify_stt.py   # STT：out.wav を文字起こし → テキスト表示
.venv/bin/python scripts/verify_llm.py   # LLM：会話を 1 ラウンド実行
```

## 📁 プロジェクト構成

```
main.py              # CLI エントリ：VAD 録音 → STT → LLM → TTS → 再生のループ
webui.py             # リアルタイム WebUI：FastAPI + WebSocket、同一パイプライン
saam/
  vad.py             # VADSegmenter（ストリーミング分割）+ MicVAD（マイクラッパー）
  stt.py             # mlx-whisper ラッパー
  llm.py             # mlx-lm ラッパー：マルチターン会話、ストリーミング出力
  tts.py             # mlx-audio Qwen3-TTS ラッパー
scripts/             # 各ステージの独立検証スクリプト
requirements.txt     # 固定された依存関係（uv pip freeze）
```

## 🛠️ 技術スタック

| ステージ | ソリューション | モデル |
| --- | --- | --- |
| VAD | [silero-vad](https://github.com/snakers4/silero-vad)（ONNX、onnxruntime 推論） | 内蔵 |
| STT | [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) | `whisper-large-v3-turbo` |
| LLM | [mlx-lm](https://github.com/ml-explore/mlx-lm) | `Qwen3-0.6B-4bit` |
| TTS | [mlx-audio](https://github.com/Blaizzy/mlx-audio) | `Qwen3-TTS-12Hz-0.6B-Base-8bit` |

> [!TIP]
> 実践で見つかった 2 つの落とし穴は本プロジェクトで解決済みです：Qwen3 はデフォルトで `<think>` 推論過程を出力します（TTS が思考内容まで読み上げてしまう）が、`enable_thinking=False` で無効化。lightning-whisper-mlx 0.0.10 は mlx 0.32 と非互換のため、STT には公式メンテナンスの mlx-whisper を採用しています。

参考プロジェクト：[huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech)

## ❓ よくある質問

**対応言語は？**
認識側の Whisper は多言語対応です —— `--language en`、`ja`、`ko` などで切り替え（デフォルト `zh`）。LLM（Qwen3）と Qwen3-TTS は中国語・英語が最も安定しています。

**エージェントが「思考内容」まで読み上げる。**
Qwen3 はデフォルトで `<think>` 推論を出力しますが、saam は `enable_thinking=False` で無効化済みです。他の推論モデルに差し替える場合は、TTS に渡す前に思考タグを除去してください。

**初回実行がとても遅い。**
初回のみモデル（約 3GB）をダウンロードするためです。以降の起動は数秒です。HuggingFace が遅い場合は `HF_ENDPOINT=https://hf-mirror.com` を試してください。

**マイクが反応しない。**
システム設定 → プライバシーとセキュリティ → マイク でターミナルとブラウザを許可してください。ブラウザのマイク利用は `localhost` / `127.0.0.1`（または HTTPS）でのアクセスが必須です。

**ポート 7860 が "Address already in use"？**
`--port 7861` で変更するか、`lsof -nP -iTCP:7860 -sTCP:LISTEN` で残留プロセスを確認してください。

## 🗺️ ロードマップ

- [x] 環境：uv + Python 3.12 venv
- [x] VAD：silero-vad によるリアルタイム音声セグメンテーション
- [x] STT / LLM / TTS のステップごとの検証
- [x] 統合：録音 → STT → LLM → TTS → 再生のループ会話
- [x] リアルタイム WebUI（WebSocket ストリーミング + 自動セグメント）
- [ ] barge-in：応答再生中のユーザー割り込み検出（[#1](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/1)）
- [ ] TTS の生成しながら再生（`stream=True`）で初音レイテンシを削減（[#2](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/2)）
- [ ] CustomVoice モデル：より多くの声と感情指示（[#3](https://github.com/tangquanwei/simple-audio-agent-on-mac/issues/3)）

---

<div align="center">

🍎 Made with MLX on Apple Silicon · あなたの言葉は、すべてあなたのマシンの中に

</div>
