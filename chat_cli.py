import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

sys.stdout.reconfigure(errors="replace")   # Windows 重定向输出时是 GBK，人设里的 emoji 会崩溃

load_dotenv()
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url=os.getenv("API_BASE_URL", "https://api.deepseek.com/v1"))

SYSTEM = """你是用户的英语口语陪练 partner，母语为英语，中文仅用于解释语法。

任务：围绕用户选择的场景（点餐/机场/面试/闲聊）进行英语对话；每轮先用英语自然回应，再附纠错区。

语气：鼓励式，像耐心的朋友；英语用词难度贴合用户水平（先测试再调整）。

边界：不代替用户完成整段作业或考试作文；用户要求全中文聊天时，提醒这是英语练习并回到场景。

输出格式：每轮固定两栏——「Reply:」英语回应；「📝 Corrections:」列出用户上轮的错误（原文 → 修改 → 一句话原因），没有错误就写 Great job!
"""

messages = [{"role": "system", "content": SYSTEM}]

while True:
    text = input("\n你: ").strip()
    if text in ("exit", "quit"):
        break
    messages.append({"role": "user", "content": text})
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat", messages=messages, temperature=0.7)
    except Exception as e:
        print("API 出错：", e); messages.pop(); continue
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
    print("机器人:", reply)
