import json
import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

PERSONA_NAME = "英语口语陪练"
KEEP_ROUNDS = 10          # 滑动窗口：只保留最近 10 轮（20 条消息）

# deepseek-flash 价目（元 / 百万 token），高峰时段价，来源 platform.deepseek.com/pricing。
# 空闲时段减半；deepseek-chat 目前是 deepseek-flash 的别名（接口返回的 model 字段即 deepseek-flash）。
PRICE_CACHE_HIT_PER_M = 0.04     # 输入·缓存命中
PRICE_CACHE_MISS_PER_M = 2.0     # 输入·缓存未命中
PRICE_OUTPUT_PER_M = 8.0         # 输出

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chat_log.jsonl")

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("API_BASE_URL", "https://api.deepseek.com/v1"))

SYSTEM = """你是用户的英语口语陪练 partner，母语为英语，中文仅用于解释语法。

任务：围绕用户选择的场景（点餐/机场/面试/闲聊）进行英语对话；每轮先用英语自然回应，再附纠错区。

语气：鼓励式，像耐心的朋友；英语用词难度贴合用户水平（先测试再调整）。

边界：不代替用户完成整段作业或考试作文；用户要求全中文聊天时，提醒这是英语练习并回到场景。

输出格式：每轮固定两栏——「Reply:」英语回应；「📝 Corrections:」列出用户上轮的错误（原文 → 修改 → 一句话原因），没有错误就写 Great job!
"""


def trim(messages, keep_rounds=KEEP_ROUNDS):
    system = messages[0]
    recent = messages[1:][-keep_rounds * 2:]
    return [system] + recent


def call_api_stream(messages, placeholder):
    stream = client.chat.completions.create(
        model="deepseek-chat", messages=trim(messages),
        temperature=0.7, stream=True,
        stream_options={"include_usage": True})
    full, usage = "", None
    for chunk in stream:
        if getattr(chunk, "usage", None):
            usage = chunk.usage          # 流式下用量在最后一块返回
        if chunk.choices:
            piece = chunk.choices[0].delta.content or ""
            full += piece
            placeholder.markdown(full)
    return full, usage   # 结束后务必把 full 追加进 messages！


def log_round(user_text, reply, usage):
    record = {
        "time": datetime.now().isoformat(timespec="seconds"),
        "user": user_text,
        "assistant": reply,
        "prompt_tokens": getattr(usage, "prompt_tokens", None),
        "completion_tokens": getattr(usage, "completion_tokens", None),
        "cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", None),
        "cache_miss_tokens": getattr(usage, "prompt_cache_miss_tokens", None),
    }
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def add_usage(usage):
    """把一轮的用量累加进本会话统计，并按 deepseek-flash 高峰价估算花费。"""
    s = st.session_state.stats
    s["rounds"] += 1
    if not usage:
        return
    hit = getattr(usage, "prompt_cache_hit_tokens", 0) or 0
    miss = getattr(usage, "prompt_cache_miss_tokens", 0) or 0
    s["prompt_tokens"] += usage.prompt_tokens
    s["completion_tokens"] += usage.completion_tokens
    s["cost"] += (hit * PRICE_CACHE_HIT_PER_M
                  + miss * PRICE_CACHE_MISS_PER_M
                  + usage.completion_tokens * PRICE_OUTPUT_PER_M) / 1e6


def to_markdown(messages):
    lines = [f"# {PERSONA_NAME} 对话记录", ""]
    for m in messages:
        if m["role"] == "system":
            continue
        who = "你" if m["role"] == "user" else "机器人"
        lines += [f"**{who}：** {m['content']}", ""]
    return "\n".join(lines)


st.set_page_config(page_title=PERSONA_NAME, page_icon="☕")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM}]
if "stats" not in st.session_state:
    st.session_state.stats = {"rounds": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}

st.title(PERSONA_NAME)

for m in st.session_state.messages:
    if m["role"] != "system":
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

if prompt := st.chat_input("说点什么…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        try:
            with st.spinner("正在生成回复…"):
                reply, usage = call_api_stream(st.session_state.messages, placeholder)
        except Exception as e:
            placeholder.empty()
            st.error(f"API 出错：{e}")
            st.session_state.messages.pop()      # 失败时回滚这条用户消息，方便重发
        else:
            st.session_state.messages.append({"role": "assistant", "content": reply})
            log_round(prompt, reply, usage)
            add_usage(usage)

# 侧边栏放在本轮对话处理之后：Streamlit 从上往下执行，只有这样才能在同一屏显示最新统计。
with st.sidebar:
    st.subheader(PERSONA_NAME)
    st.caption(f"只记得最近 {KEEP_ROUNDS} 轮对话；清空对话会同时重置统计")

    st.divider()
    s = st.session_state.stats
    st.metric("本会话轮数", s["rounds"])
    st.metric("累计输入 Token", f'{s["prompt_tokens"]:,}')
    st.metric("累计输出 Token", f'{s["completion_tokens"]:,}')
    st.metric("估算花费", f"¥{s['cost']:.4f}")
    st.caption(f"deepseek-flash 高峰价：缓存命中 ¥{PRICE_CACHE_HIT_PER_M}、"
               f"未命中 ¥{PRICE_CACHE_MISS_PER_M}、输出 ¥{PRICE_OUTPUT_PER_M} 每百万 token")

    st.divider()
    st.download_button("导出对话", data=to_markdown(st.session_state.messages),
                       file_name="chat.md", mime="text/markdown", width="stretch")
    if st.button("清空对话", width="stretch"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM}]
        st.session_state.stats = {"rounds": 0, "prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
        st.rerun()
