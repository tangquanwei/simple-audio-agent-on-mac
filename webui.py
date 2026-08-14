#!/usr/bin/env python
"""实时语音 WebUI：浏览器持续推麦克风流，服务端 VAD 检测说话结束自动回答。

用法：
    .venv/bin/python webui.py
然后打开 http://127.0.0.1:7860 ，点「开始对话」后直接说话即可。
"""
import argparse
import asyncio
import base64
import io

import numpy as np
import soundfile as sf
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from saam.llm import LLM
from saam.stt import STT
from saam.tts import TTS
from saam.vad import VADSegmenter

PAGE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>saam</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #fbfbfd;
    --text: #1d1d1f;
    --dim: #86868b;
    --bot: #e9e9eb;
    --bot-text: #1d1d1f;
    --user: #007aff;
    --hairline: rgba(0, 0, 0, .08);
    --glass: rgba(251, 251, 253, .72);
    --idle: #d1d1d6;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #000;
      --text: #f5f5f7;
      --dim: #86868b;
      --bot: #26262a;
      --bot-text: #f5f5f7;
      --hairline: rgba(255, 255, 255, .12);
      --glass: rgba(0, 0, 0, .6);
      --idle: #3a3a3c;
    }
  }
  * { box-sizing: border-box; margin: 0; }
  html, body { height: 100%; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro SC", "PingFang SC", "Helvetica Neue", sans-serif;
    background: var(--bg); color: var(--text);
    display: flex; flex-direction: column; align-items: center;
    overflow: hidden;
    -webkit-font-smoothing: antialiased;
  }

  /* ── 对话区 ─────────────────────────── */
  #log {
    flex: 1; width: 100%; max-width: 640px; overflow-y: auto;
    padding: 2rem 1.25rem 1.5rem;
    display: flex; flex-direction: column; gap: .55rem;
    scroll-behavior: smooth;
    mask-image: linear-gradient(transparent, #000 32px);
  }
  #log::-webkit-scrollbar { display: none; }
  #hero {
    margin: auto; text-align: center; color: var(--dim);
    font-size: 1.6rem; font-weight: 600; letter-spacing: .01em;
    animation: fade .8s ease;
  }
  #hero small { display: block; margin-top: .6rem; font-size: .85rem; font-weight: 400; }
  .msg {
    max-width: 78%; padding: .5rem .9rem; border-radius: 18px;
    font-size: .95rem; line-height: 1.45; white-space: pre-wrap; word-break: break-word;
    animation: rise .3s cubic-bezier(.25, .9, .3, 1.2);
  }
  @keyframes rise { from { opacity: 0; transform: translateY(8px) scale(.97); } }
  @keyframes fade { from { opacity: 0; } }
  .user { align-self: flex-end; background: var(--user); color: #fff; border-bottom-right-radius: 4px; }
  .bot  { align-self: flex-start; background: var(--bot); color: var(--bot-text); border-bottom-left-radius: 4px; }
  .sys  { align-self: center; color: var(--dim); font-size: .75rem; animation: fade .4s ease; }

  /* ── 底部磨砂栏 ─────────────────────── */
  footer {
    width: 100%; padding: 1rem 0 calc(1.2rem + env(safe-area-inset-bottom));
    display: flex; flex-direction: column; align-items: center; gap: .55rem;
    background: var(--glass);
    -webkit-backdrop-filter: saturate(180%) blur(20px);
    backdrop-filter: saturate(180%) blur(20px);
    border-top: .5px solid var(--hairline);
  }

  /* ── Siri 流光球 ────────────────────── */
  #orb {
    width: 72px; height: 72px; border-radius: 50%; border: none; cursor: pointer;
    position: relative; overflow: hidden; background: var(--idle);
    display: grid; place-items: center;
    transition: transform .35s cubic-bezier(.34, 1.4, .64, 1), background .4s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, .12);
  }
  #orb:hover { transform: scale(1.05); }
  #orb:active { transform: scale(.94); }
  #orb svg { width: 26px; height: 26px; fill: #fff; opacity: .9; transition: opacity .3s; }
  #orb i {
    position: absolute; inset: -45%; border-radius: 50%;
    filter: blur(14px) saturate(140%); opacity: 0; transition: opacity .45s ease;
    pointer-events: none;
  }
  #orb .a { background: conic-gradient(#ff5fa2, #a06bff, #57c7ff, #6effc9, #ff5fa2); animation: rot 7s linear infinite; }
  #orb .b { background: conic-gradient(#57c7ff, #7d5aff, #ff8fb1, #ffd15f, #57c7ff); animation: rot 4.5s linear infinite reverse; }
  #orb .c { background: radial-gradient(circle at 32% 28%, rgba(255,255,255,.55), transparent 55%); filter: none; }
  @keyframes rot { to { transform: rotate(360deg); } }
  #orb.on { background: #1d1d1f; box-shadow: 0 6px 24px rgba(120, 100, 255, .35); animation: breathe 3.2s ease-in-out infinite; }
  #orb.on i { opacity: 1; }
  #orb.on svg { opacity: 0; }
  @keyframes breathe { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.045); } }
  #orb.busy .a { animation-duration: 1.8s; }
  #orb.busy .b { animation-duration: 1.2s; }
  #orb.speaking { animation: talk .8s ease-in-out infinite; }
  @keyframes talk { 0%, 100% { transform: scale(1); } 30% { transform: scale(1.1); } 60% { transform: scale(.97); } }

  #hint {
    font-size: .8rem; color: var(--dim); letter-spacing: .02em;
    min-height: 1.1em; transition: color .3s;
  }
</style>
</head>
<body>
<div id="log">
  <div id="hero">有什么可以帮你？<small>点按下方，直接开口说话</small></div>
</div>
<footer>
  <button id="orb" aria-label="开始对话">
    <i class="a"></i><i class="b"></i><i class="c"></i>
    <svg viewBox="0 0 24 24"><path d="M12 15a3 3 0 0 0 3-3V6a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-2.08A7 7 0 0 0 19 12h-2z"/></svg>
  </button>
  <div id="hint">点按开始</div>
</footer>
<script>
const orb = document.getElementById('orb');
const hint = document.getElementById('hint');
const log = document.getElementById('log');
let ws = null, audioCtx = null, muted = false;

function add(role, text) {
  const hero = document.getElementById('hero');
  if (hero) hero.remove();
  const d = document.createElement('div');
  d.className = 'msg ' + role;
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
}
function setState(label, busy, speaking) {
  hint.textContent = label;
  orb.classList.toggle('busy', !!busy);
  orb.classList.toggle('speaking', !!speaking);
}

async function start() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.binaryType = 'arraybuffer';
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'status' && msg.value === 'busy') {
      muted = true; setState('正在思考…', true, false);
    } else if (msg.type === 'reply') {
      if (msg.text) add('user', msg.text);
      add('bot', msg.reply);
      setState('', false, true);
      const audio = new Audio('data:audio/wav;base64,' + msg.audio);
      audio.onended = () => { muted = false; setState('正在聆听', false, false); };
      audio.play();
    } else if (msg.type === 'error') {
      add('sys', msg.message); muted = false; setState('正在聆听', false, false);
    }
  };
  ws.onclose = () => stop(true);

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  audioCtx = new AudioContext({ sampleRate: 16000 });
  const src = audioCtx.createMediaStreamSource(stream);
  const proc = audioCtx.createScriptProcessor(4096, 1, 1);
  proc.onaudioprocess = (e) => {
    if (muted || !ws || ws.readyState !== 1) return;
    const input = e.inputBuffer.getChannelData(0);
    // 个别浏览器忽略 sampleRate 约束，需要重采样到 16kHz
    const ratio = audioCtx.sampleRate / 16000;
    const out = ratio === 1 ? input : resample(input, ratio);
    ws.send(out.buffer.slice(out.byteOffset, out.byteOffset + out.byteLength));
  };
  src.connect(proc);
  proc.connect(audioCtx.destination);
  audioCtx._stream = stream; audioCtx._proc = proc;

  const hero = document.getElementById('hero');
  if (hero) hero.querySelector('small').textContent = '说完停顿一下，助手就会回答';
  orb.classList.add('on');
  setState('正在聆听', false, false);
}

function resample(input, ratio) {
  const n = Math.floor(input.length / ratio);
  const out = new Float32Array(n);
  for (let i = 0; i < n; i++) out[i] = input[Math.floor(i * ratio)];
  return out;
}

function stop(closed) {
  if (audioCtx) {
    audioCtx._proc.disconnect();
    audioCtx._stream.getTracks().forEach(t => t.stop());
    audioCtx.close(); audioCtx = null;
  }
  if (ws && !closed) ws.close();
  ws = null; muted = false;
  orb.classList.remove('on');
  setState('点按开始', false, false);
}

orb.onclick = () => ws ? stop(false) : start();
</script>
</body>
</html>
"""


def create_app(stt_model, llm_model, tts_model, voice, language):
    app = FastAPI()
    stt = STT(stt_model, language)
    llm = LLM(llm_model)
    tts = TTS(tts_model, voice)
    lock = asyncio.Lock()

    def run_pipeline(audio):
        text = stt.transcribe(audio)
        if not text:
            return None
        reply = llm.chat(text)
        wav, sr = tts.synthesize(reply)
        buf = io.BytesIO()
        sf.write(buf, wav, sr, format="WAV")
        return {"type": "reply", "text": text, "reply": reply,
                "audio": base64.b64encode(buf.getvalue()).decode()}

    @app.get("/", response_class=HTMLResponse)
    def index():
        return PAGE

    @app.websocket("/ws")
    async def ws_endpoint(ws: WebSocket):
        await ws.accept()
        segmenter = VADSegmenter()
        loop = asyncio.get_running_loop()
        try:
            while True:
                data = await ws.receive_bytes()
                segment = segmenter.feed(np.frombuffer(data, dtype=np.float32))
                if segment is None:
                    continue
                await ws.send_json({"type": "status", "value": "busy"})
                async with lock:  # 模型推理串行，支持多个浏览器连接排队
                    result = await loop.run_in_executor(None, run_pipeline, segment)
                if result is None:
                    await ws.send_json({"type": "error", "message": "未识别到语音"})
                else:
                    await ws.send_json(result)
        except WebSocketDisconnect:
            pass

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stt-model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--llm-model", default="mlx-community/Qwen3-0.6B-4bit")
    parser.add_argument("--tts-model", default="mlx-community/Qwen3-TTS-12Hz-0.6B-Base-8bit")
    parser.add_argument("--voice", default="serena")
    parser.add_argument("--language", default="zh")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=7860)
    args = parser.parse_args()

    print("加载模型中（首次运行会下载）...")
    app = create_app(args.stt_model, args.llm_model, args.tts_model, args.voice, args.language)
    print(f"就绪，打开 http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
