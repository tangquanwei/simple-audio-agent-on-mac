"""LLM：mlx-lm 加载 Qwen3，维护多轮对话，流式生成。"""
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

SYSTEM_PROMPT = "你是一个语音助手。回复要简短、口语化，用中文回复纯文本。"


class LLM:
    def __init__(self, model="mlx-community/Qwen3-0.6B-4bit", max_tokens=256):
        self.model, self.tokenizer = load(model)
        self.max_tokens = max_tokens
        self.sampler = make_sampler(temp=0.7, top_p=0.8)
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def chat(self, user_text, on_token=None):
        self.messages.append({"role": "user", "content": user_text})
        prompt = self.tokenizer.apply_chat_template(
            self.messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=False,
        )
        text = ""
        for resp in stream_generate(
            self.model, self.tokenizer, prompt,
            max_tokens=self.max_tokens, sampler=self.sampler,
        ):
            text += resp.text
            if on_token is not None:
                on_token(resp.text)
        self.messages.append({"role": "assistant", "content": text})
        return text
