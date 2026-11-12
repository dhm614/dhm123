#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
clean.py —— 对 crawler.py 采到的数据做清洗，并把完整过程写进 clean_log.txt。

用法:
    python clean.py                                  # 自动找最新的 data_quotes_*.csv
    python clean.py data_quotes_20261106.csv         # 指定输入
    python clean.py --in a.csv --out b.csv           # 指定输入输出

清洗四项（对应课程要求 3.2）:
    ① 去重：按 text 全文去重，记录删除条数
    ② 补空：author 空 → 「未知」；tags 空 → 「无标签」；分别计数
    ③ 统一格式：text 首尾去空白、内部连续空白压成一个；author_url 补全为绝对地址；tags 统一用 | 分隔
    ④ 极值校验：每列非空率、text 长度 min/max、长度 <5 的行单独列出人工确认

每一步都打印处理前后的行数；结果另存 data_quotes_clean_日期.csv（utf-8-sig）。
"""

import argparse
import csv
import glob
import os
import re
import sys
from datetime import datetime

FIELDS = ["text", "author", "author_url", "tags", "page"]
BASE_URL = "https://quotes.toscrape.com"
LOG = []          # 收集日志行，最后整体写文件


# ---------------------------------------------------------------- 日志
def log(msg=""):
    print(msg)
    LOG.append(msg)


def section(title):
    log()
    log(title)
    log("-" * 62)


# ---------------------------------------------------------------- 读写
def find_latest(pattern="data_quotes_*.csv"):
    files = [f for f in glob.glob(pattern) if "clean" not in os.path.basename(f)]
    if not files:
        sys.exit("[错误] 找不到 data_quotes_*.csv，请先运行: python crawler.py --full")
    return max(files, key=os.path.getmtime)


def load(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def save(rows, path):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------- ① 去重
def step1_dedup(rows):
    section("① 去重：按 text 全文去重")
    before = len(rows)
    seen, kept, removed = set(), [], []

    for r in rows:
        key = r["text"]
        if key in seen:
            removed.append(key)
            continue
        seen.add(key)
        kept.append(r)

    log(f"  处理前行数 : {before}")
    log(f"  重复条数   : {len(removed)}")
    log(f"  处理行后数 : {len(kept)}")
    for t in removed[:5]:
        log(f"    重复示例 : {t[:50]}")
    return kept, {"before": before, "removed": len(removed), "after": len(kept)}


# ---------------------------------------------------------------- ② 补空
def step2_fill(rows):
    section("② 补空：author 空 → 「未知」，tags 空 → 「无标签」")
    before = len(rows)
    n_author = n_tags = 0

    for r in rows:
        if not r["author"].strip():
            r["author"] = "未知"
            n_author += 1
        if not r["tags"].strip():
            r["tags"] = "无标签"
            n_tags += 1

    log(f"  处理前行数              : {before}")
    log(f"  author 为空 → 补「未知」 : {n_author} 条")
    log(f"  tags 为空 → 补「无标签」 : {n_tags} 条")
    log(f"  处理行后数              : {len(rows)}")
    return rows, {"author": n_author, "tags": n_tags, "before": before, "after": len(rows)}


# ---------------------------------------------------------------- ③ 统一格式
def step3_normalize(rows):
    section("③ 统一格式：text 去空白/压空格、author_url 补全、tags 统一 |")
    before = len(rows)
    n_text = n_url = n_tag = 0

    for r in rows:
        # text：首尾去空白 + 内部连续空白压成一个
        old_text = r["text"]
        new_text = re.sub(r"\s+", " ", old_text).strip()
        if new_text != old_text:
            n_text += 1
        r["text"] = new_text

        # author_url：相对路径补成绝对地址
        url = r["author_url"].strip()
        if url and not url.startswith("http"):
            r["author_url"] = BASE_URL + ("" if url.startswith("/") else "/") + url
            n_url += 1

        # tags：分隔符统一为 |，去掉多余空格
        parts = [t.strip() for t in re.split(r"[|,;，；]", r["tags"]) if t.strip()]
        new_tags = "|".join(parts) if parts else "无标签"
        if new_tags != r["tags"]:
            n_tag += 1
        r["tags"] = new_tags

    log(f"  处理前行数                    : {before}")
    log(f"  text 规范化改动               : {n_text} 条")
    log(f"  author_url 补全为绝对地址     : {n_url} 条")
    log(f"  tags 分隔符统一为 |           : {n_tag} 条")
    log(f"  处理行后数                    : {len(rows)}")
    return rows, {"text": n_text, "url": n_url, "tags": n_tag,
                  "before": before, "after": len(rows)}


# ---------------------------------------------------------------- ④ 极值校验
def step4_check(rows):
    section("④ 极值校验：非空率 / 长度分布 / 异常行")
    total = len(rows)
    if total == 0:
        log("  [警告] 数据为空，跳过校验")
        return {"short": 0}

    for field in FIELDS:
        nonempty = sum(1 for r in rows if str(r[field]).strip())
        log(f"  {field:<11} 非空率: {nonempty}/{total} = {nonempty / total * 100:.1f}%")

    lengths = [len(r["text"]) for r in rows]
    avg = sum(lengths) / total
    log(f"  text 长度 min = {min(lengths)}  max = {max(lengths)}  平均 = {avg:.1f}")

    short = [(i, len(r["text"]), r["text"]) for i, r in enumerate(rows, 1) if len(r["text"]) < 5]
    log(f"  text 长度 < 5 的行: {len(short)} 条" + ("（需人工确认）" if short else "（无异常）"))
    for idx, ln, txt in short:
        log(f"    第{idx}行  长度{ln}  内容={txt!r}")

    pages = sorted({int(r["page"]) for r in rows if str(r["page"]).strip().isdigit()})
    log(f"  page 分布: {pages}  共 {len(pages)} 页，平均每页 {total / max(len(pages), 1):.1f} 条")

    return {"short": len(short), "min": min(lengths), "max": max(lengths),
            "avg": avg, "pages": pages}


# ---------------------------------------------------------------- 主流程
def main():
    parser = argparse.ArgumentParser(description="数据清洗：去重 / 补空 / 统一格式 / 极值校验")
    parser.add_argument("input", nargs="?", help="输入 CSV（默认自动找最新的 data_quotes_*.csv）")
    parser.add_argument("--in", dest="infile", help="同 input")
    parser.add_argument("--out", dest="outfile", help="输出 CSV（默认 data_quotes_clean_日期.csv）")
    args = parser.parse_args()

    infile = args.input or args.infile or find_latest()
    if not os.path.exists(infile):
        sys.exit(f"[错误] 输入文件不存在: {infile}")

    # 输出文件名：从输入名里取日期，保持 data_quotes_<日期>.csv → data_quotes_clean_<日期>.csv
    m = re.search(r"(\d{8})", os.path.basename(infile))
    datestr = m.group(1) if m else datetime.now().strftime("%Y%m%d")
    outfile = args.outfile or f"data_quotes_clean_{datestr}.csv"

    log("=" * 62)
    log("数据清洗日志 (clean_log.txt)")
    log(f"运行时间 : {datetime.now():%Y-%m-%d %H:%M:%S}")
    log(f"输入文件 : {infile}")
    log(f"输出文件 : {outfile}")
    log(f"字段清单 : {' / '.join(FIELDS)}")
    log("=" * 62)

    rows = load(infile)
    log(f"[读入] {len(rows)} 条数据，列: {list(rows[0].keys()) if rows else '空文件'}")

    rows, s1 = step1_dedup(rows)
    rows, s2 = step2_fill(rows)
    rows, s3 = step3_normalize(rows)
    s4 = step4_check(rows)

    save(rows, outfile)

    section("汇总")
    log(f"  初始条数     : {s1['before']}")
    log(f"  去重删除     : {s1['removed']} 条")
    log(f"  补 author    : {s2['author']} 条")
    log(f"  补 tags      : {s2['tags']} 条")
    log(f"  最终条数     : {len(rows)}")
    log(f"  输出文件     : {outfile}（utf-8-sig）")
    log("=" * 62)
    log("[完成] 清洗日志已写入 clean_log.txt")

    with open("clean_log.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
