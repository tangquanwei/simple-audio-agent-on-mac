"""验证 LLM：Qwen3-0.6B 本地推理，跑一轮中文对话。"""
import argparse
import time

from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

DEFAULT_MODEL = "mlx-community/Qwen3-0.6B-4bit"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt", default="用一两句话介绍一下你自己。")
    args = parser.parse_args()

    t0 = time.perf_counter()
    model, tokenizer = load(args.model)
    print(f"[llm] 模型加载 {time.perf_counter() - t0:.1f}s")

    messages = [
        {"role": "system", "content": "你是一个语音助手，回复简短、口语化，用中文。"},
        {"role": "user", "content": args.prompt},
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )

    sampler = make_sampler(temp=0.7, top_p=0.8)
    print("[llm] 回复: ", end="", flush=True)
    t0 = time.perf_counter()
    text = ""
    for resp in stream_generate(model, tokenizer, prompt, max_tokens=256, sampler=sampler):
        print(resp.text, end="", flush=True)
        text += resp.text
    print(f"\n[llm] 生成 {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
