"""命令行问答脚本：加载 index.json，向量检索 Top3 后调用对话模型作答。

用法：python ask.py

环境变量（.env）：
    EMBEDDING_MODEL                     必填，须与建库时一致
    EMBEDDING_KEY  / DEEPSEEK_API_KEY   任一必填
    EMBEDDING_BASE_URL / API_BASE_URL   任一必填，OpenAI 兼容的 /v1 基地址
    CHAT_MODEL                          可选，默认 deepseek-chat
    CHAT_KEY  / DEEPSEEK_API_KEY        任一必填，对话模型使用
    CHAT_BASE_URL / API_BASE_URL        任一必填，对话模型使用
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import requests
from dotenv import load_dotenv

INDEX_PATH = "index.json"
TOP_K = 3
DEFAULT_CHAT_MODEL = "deepseek-chat"
TEMPERATURE = 0.2
REQUEST_TIMEOUT = 60
SYSTEM_PROMPT = "只根据资料回答；资料不足时明确说资料中未找到；末尾用【来源：文件名·块id】标注"


def env_first(*names: str) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def load_config() -> dict[str, str]:
    load_dotenv()
    cfg = {
        "embed_key": env_first("EMBEDDING_KEY", "DEEPSEEK_API_KEY"),
        "embed_base": env_first("EMBEDDING_BASE_URL", "API_BASE_URL"),
        "embed_model": os.getenv("EMBEDDING_MODEL"),
        "chat_key": env_first("CHAT_KEY", "DEEPSEEK_API_KEY"),
        "chat_base": env_first("CHAT_BASE_URL", "API_BASE_URL"),
        "chat_model": env_first("CHAT_MODEL") or DEFAULT_CHAT_MODEL,
    }
    labels = {
        "embed_key": "EMBEDDING_KEY 或 DEEPSEEK_API_KEY",
        "embed_base": "EMBEDDING_BASE_URL 或 API_BASE_URL",
        "embed_model": "EMBEDDING_MODEL",
        "chat_key": "CHAT_KEY 或 DEEPSEEK_API_KEY",
        "chat_base": "CHAT_BASE_URL 或 API_BASE_URL",
        "chat_model": "CHAT_MODEL",
    }
    missing = [labels[key] for key, value in cfg.items() if not value]
    if missing:
        sys.exit("缺少环境变量：" + "、".join(missing))
    return cfg


def embed_query(text: str, cfg: dict[str, str]) -> list[float]:
    """把问题转成向量，使用与建库相同的模型。"""
    resp = requests.post(
        cfg["embed_base"].rstrip("/") + "/embeddings",
        headers={"Authorization": f"Bearer {cfg['embed_key']}"},
        json={"model": cfg["embed_model"], "input": [text]},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["data"][0]["embedding"]


def search(question_vec: list[float], chunks: list[dict], top_k: int = TOP_K) -> list[tuple[dict, float]]:
    """余弦相似度排序，返回 [(块, 分数)] 降序前 top_k 条。"""
    matrix = np.array([chunk["vec"] for chunk in chunks], dtype=np.float64)
    query = np.array(question_vec, dtype=np.float64)
    scores = matrix @ query / (np.linalg.norm(matrix, axis=1) * np.linalg.norm(query))
    order = np.argsort(-scores)[:top_k]
    return [(chunks[int(i)], float(scores[int(i)])) for i in order]


def build_messages(question: str, hits: list[tuple[dict, float]]) -> list[dict[str, str]]:
    lines = ["资料："]
    for rank, (chunk, _score) in enumerate(hits, 1):
        name = Path(chunk["source"]).name
        lines.append(f"\n【资料{rank}】文件名：{name} · 块id：{chunk['id']}\n{chunk['text']}")
    lines.append(f"\n问题：{question}")
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(lines)},
    ]


def chat(messages: list[dict[str, str]], cfg: dict[str, str]) -> str:
    resp = requests.post(
        cfg["chat_base"].rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {cfg['chat_key']}"},
        json={"model": cfg["chat_model"], "messages": messages, "temperature": TEMPERATURE},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def main() -> None:
    cfg = load_config()
    if not Path(INDEX_PATH).exists():
        sys.exit(f"未找到 {INDEX_PATH}，请先运行 python index.py 建库")
    chunks = json.loads(Path(INDEX_PATH).read_text(encoding="utf-8"))
    print(
        f"已加载 {INDEX_PATH}：{len(chunks)} 块"
        f"（问题向量模型 {cfg['embed_model']}，对话模型 {cfg['chat_model']}）"
    )

    while True:
        try:
            question = input("\n提问（输入 q 退出）> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() == "q":
            break
        if not question:
            continue

        try:
            hits = search(embed_query(question, cfg), chunks)
        except Exception as exc:
            print(f"[错误] 检索失败：{exc}")
            continue

        print("检索结果：")
        for rank, (chunk, score) in enumerate(hits, 1):
            print(f"  {rank}. 来源 {chunk['source']} · {chunk['id']} · 相似度 {score:.4f}")

        try:
            answer = chat(build_messages(question, hits), cfg)
        except Exception as exc:
            print(f"[错误] 对话请求失败：{exc}")
            continue
        print(f"\n{answer}")


if __name__ == "__main__":
    main()
