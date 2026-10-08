import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

PERSONA_NAME = "英语口语陪练"
KEEP_ROUNDS = 10          # 滑动窗口：只保留最近 10 轮（20 条消息）

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
        temperature=0.7, stream=True)
    full = ""
    for chunk in stream:
        piece = chunk.choices[0].delta.content or ""
        full += piece
        placeholder.markdown(full)
    return full   # 结束后务必把 full 追加进 messages！


st.set_page_config(page_title=PERSONA_NAME, page_icon="☕")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM}]

with st.sidebar:
    st.subheader(PERSONA_NAME)
    st.caption(f"只记得最近 {KEEP_ROUNDS} 轮对话")
    if st.button("清空对话", width="stretch"):
        st.session_state.messages = [{"role": "system", "content": SYSTEM}]
        st.rerun()

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
                reply = call_api_stream(st.session_state.messages, placeholder)
        except Exception as e:
            placeholder.empty()
            st.error(f"API 出错：{e}")
            st.session_state.messages.pop()      # 失败时回滚这条用户消息，方便重发
        else:
            st.session_state.messages.append({"role": "assistant", "content": reply})
