"""离线建库脚本：读取 docs/ 下的文本，切块后调用 Embedding API，写出 index.json。

用法：python index.py

环境变量（.env）：
    EMBEDDING_MODEL                    必填
    EMBEDDING_KEY  / DEEPSEEK_API_KEY   任一必填
    EMBEDDING_BASE_URL / API_BASE_URL   任一必填，OpenAI 兼容的 /v1 基地址
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

DOCS_DIR = "docs"
INDEX_PATH = "index.json"
SUFFIXES = {".txt", ".md"}
SIZE = 400
OVERLAP = 60
# 百炼 text-embedding-v4 单次上限 10 条（超过会返回 InvalidParameter），其余服务也满足
BATCH_SIZE = 10
REQUEST_TIMEOUT = 60


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """固定长度滑窗切分：块长 size，相邻重叠 overlap，末尾余下部分作为最后一块。"""
    if size <= overlap:
        raise ValueError("size 必须大于 overlap")
    step = size - overlap
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += step
    return chunks


def read_docs(docs_dir: str = DOCS_DIR) -> list[tuple[str, str]]:
    """读取 docs/ 下全部 txt/md，返回按路径排序的 (相对路径, 文本) 列表。"""
    docs: list[tuple[str, str]] = []
    for path in sorted(Path(docs_dir).rglob("*")):
        if path.is_file() and path.suffix.lower() in SUFFIXES:
            text = path.read_text(encoding="utf-8")
            if text.strip():
                docs.append((path.as_posix(), text))
    return docs


def embed_batch(texts: list[str], key: str, base_url: str, model: str) -> list[list[float]]:
    """调用一次 Embedding API，返回与 texts 顺序一致的向量列表；失败抛异常。"""
    resp = requests.post(
        base_url.rstrip("/") + "/embeddings",
        headers={"Authorization": f"Bearer {key}"},
        json={"model": model, "input": texts},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()["data"]
    data.sort(key=lambda item: item["index"])
    return [item["embedding"] for item in data]


def embed_batch_with_retry(
    texts: list[str], key: str, base_url: str, model: str
) -> list[list[float] | None]:
    """批量嵌入：失败重试一次，仍失败则退化为逐块调用，单块失败置 None。"""
    for attempt in (1, 2):
        try:
            return embed_batch(texts, key, base_url, model)
        except Exception as exc:
            detail = getattr(getattr(exc, "response", None), "text", "")
            print(f"[警告] 批次请求失败（第 {attempt} 次）：{exc}{' ' + detail[:200] if detail else ''}")

    vecs: list[list[float] | None] = [None] * len(texts)
    for i, text in enumerate(texts):
        try:
            vecs[i] = embed_batch([text], key, base_url, model)[0]
        except Exception as exc:
            print(f"[警告] 跳过块：{exc}")
    return vecs


def load_config() -> tuple[str, str, str]:
    load_dotenv()
    key = os.getenv("EMBEDDING_KEY") or os.getenv("DEEPSEEK_API_KEY")
    base_url = os.getenv("EMBEDDING_BASE_URL") or os.getenv("API_BASE_URL")
    model = os.getenv("EMBEDDING_MODEL")
    missing = [
        name
        for name, value in (
            ("EMBEDDING_KEY 或 DEEPSEEK_API_KEY", key),
            ("EMBEDDING_BASE_URL 或 API_BASE_URL", base_url),
            ("EMBEDDING_MODEL", model),
        )
        if not value
    ]
    if missing:
        sys.exit("缺少环境变量：" + "、".join(missing))
    return key, base_url, model


def main() -> None:
    started = time.perf_counter()
    key, base_url, model = load_config()

    records: list[dict[str, str]] = []
    total_chars = 0
    for source, text in read_docs():
        total_chars += len(text)
        for i, chunk in enumerate(chunk_text(text, SIZE, OVERLAP)):
            records.append({"id": f"{source}#{i}", "source": source, "text": chunk})

    if not records:
        sys.exit(f"{DOCS_DIR}/ 下没有可处理的 txt/md 内容")

    print(f"文件合计 {total_chars} 字，切出 {len(records)} 块，开始嵌入（每批 {BATCH_SIZE} 块）")

    chunks: list[dict] = []
    processed = 0
    skipped = 0
    for start in range(0, len(records), BATCH_SIZE):
        batch = records[start : start + BATCH_SIZE]
        vecs = embed_batch_with_retry([r["text"] for r in batch], key, base_url, model)
        for record, vec in zip(batch, vecs):
            processed += 1
            if vec is None:
                skipped += 1
            else:
                chunks.append({**record, "vec": vec})
            if processed % 10 == 0:
                print(f"进度：{processed}/{len(records)} 块")

    Path(INDEX_PATH).write_text(
        json.dumps(chunks, ensure_ascii=False), encoding="utf-8"
    )

    dims = {len(c["vec"]) for c in chunks}
    print(
        f"完成：写入 {INDEX_PATH}，共 {len(chunks)} 块"
        + (f"（跳过 {skipped} 块）" if skipped else "")
        + f"，向量维度 {sorted(dims)}，总耗时 {time.perf_counter() - started:.2f} 秒"
    )


if __name__ == "__main__":
    main()
