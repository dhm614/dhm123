#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
crawler.py —— 合规名言采集爬虫（quotes.toscrape.com）

用法:
    python crawler.py            # 默认：只采第 1 页前 5 条，打印成表格供人工核对（不写文件）
    python crawler.py --full     # 放开翻页，采前 5 页全量并存 CSV
    python crawler.py --full --pages 2   # 调试用：只采前 2 页（上限锁定 5 页）

字段: text / author / author_url / tags / page（严格一致，不做增减）
合规: 每次请求后 time.sleep(1.5)、自定义 UA、最多 5 页、串行不发并发
依赖: pip install requests beautifulsoup4 lxml
"""

import argparse
import csv
import sys
import time
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# ------------------------------------------------------------ 配置
BASE_URL = "https://quotes.toscrape.com"
USER_AGENT = "VibeCodingCourse/1.0 (student project; contact: 3133477401@qq.com)"
HEADERS = {"User-Agent": USER_AGENT}
MAX_PAGES_HARD = 5      # 合规：总页数硬上限
SLEEP_SEC = 1.5         # 合规：每次请求后休眠
RETRY_TIMES = 1         # 单页失败重试 1 次
TIMEOUT = 10            # 秒，不设超时会挂死
FIELDS = ["text", "author", "author_url", "tags", "page"]


# ------------------------------------------------------------ 工具
def _width(s):
    """按终端显示宽度计算（中文算 2 列）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _fit(s, width):
    """按显示宽度截断并右侧补空格，保证表格对齐。"""
    s = str(s)
    out, used, truncated = "", 0, False
    for ch in s:
        w = 2 if unicodedata.east_asian_width(ch) in "WF" else 1
        if used + w > width - 1:      # 预留 1 列放省略号
            truncated = True
            break
        out += ch
        used += w
    if truncated:
        out += "…"
        used += 1
    return out + " " * max(0, width - used)


# ------------------------------------------------------------ 抓取
def fetch(url, stats):
    """请求单页，返回 HTML 文本；失败重试 1 次，仍失败返回 None。

    - 每次请求（含失败与重试）结束后都会 sleep(SLEEP_SEC)
    - 403 立即终止（不做任何绕过尝试）
    """
    for attempt in range(1, RETRY_TIMES + 2):
        try:
            stats["requests"] += 1
            resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)

            if resp.status_code == 403:
                print("\n[403] 目标站点拒绝访问，按合规要求立即终止（不绕过、不换 IP、不加代理）。")
                print("     请检查 robots.txt、UA 是否合规，并加大请求间隔后人工重试。")
                sys.exit(3)
            if resp.status_code == 429:
                print("\n[429] 请求过于频繁，已触发限流，按合规要求立即终止。")
                sys.exit(3)

            resp.raise_for_status()
            return resp.text

        except SystemExit:
            raise
        except Exception as exc:
            print(f"  [警告] 第 {attempt} 次请求失败: {type(exc).__name__}: {exc}")
            if attempt <= RETRY_TIMES:
                print("  [重试] 稍后将重试 1 次 …")
        finally:
            time.sleep(SLEEP_SEC)

    return None


def parse_page(html, page):
    """把一页 HTML 解析成记录列表（严格 5 字段）。空 text 的行直接丢弃。"""
    soup = BeautifulSoup(html, "lxml")
    rows = []

    for quote in soup.select("div.quote"):
        text_el = quote.select_one("span.text")
        author_el = quote.select_one("small.author")
        link_el = quote.select_one("a[href^='/author/']")
        tag_els = quote.select("div.tags a.tag")

        text = text_el.get_text(strip=True) if text_el else ""
        if not text:                       # 验收：无空 text 字段
            continue

        author = author_el.get_text(strip=True) if author_el else ""
        author_url = BASE_URL + link_el["href"] if link_el else ""
        tags = "|".join(t.get_text(strip=True) for t in tag_els)   # 统一用 | 连接

        rows.append({
            "text": text,
            "author": author,
            "author_url": author_url,
            "tags": tags,
            "page": page,
        })

    return rows


def next_page_url(html):
    """取列表页底部「Next」链接的绝对地址；已是最后一页返回 None。"""
    a = BeautifulSoup(html, "lxml").select_one("ul.pager li.next a")
    if not a:
        return None
    href = a.get("href", "")
    return BASE_URL + href if href.startswith("/") else href


# ------------------------------------------------------------ 输出
def print_table(rows):
    """把若干条记录打印成对齐文本表格（供人工核对）。"""
    if not rows:
        print("（未解析到数据：多半是选择器失效，请到浏览器 F12 核对 div.quote 结构）")
        return

    cols = [("#", 4), ("author", 24), ("text", 46), ("tags", 20), ("page", 6)]
    line = "+".join("-" * w for _, w in cols)
    line = "+" + line + "+"

    print(line)
    print("|" + "|".join(_fit(name, w) for name, w in cols) + "|")
    print(line)
    for i, r in enumerate(rows, 1):
        cells = [str(i), r["author"], r["text"], r["tags"] or "(无标签)", str(r["page"])]
        print("|" + "|".join(_fit(v, w) for v, w in zip(cells, [w for _, w in cols])) + "|")
    print(line)


def save_csv(rows):
    """写 CSV：utf-8-sig（Excel 双击打开不乱码）。返回文件路径。"""
    fname = f"data_quotes_{datetime.now():%Y%m%d}.csv"
    with open(fname, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return fname


# ------------------------------------------------------------ 自检 / 汇总
def self_check(rows):
    """按任务验收标准做输出前自检。"""
    empty_text = sum(1 for r in rows if not r["text"].strip())
    empty_author = sum(1 for r in rows if not r["author"].strip())
    empty_tags = sum(1 for r in rows if not r["tags"].strip())
    bad_tags = sum(1 for r in rows if r["tags"] and (";" in r["tags"] or "," in r["tags"]))
    print("\n[自检] " + "-" * 46)
    print(f"  条数                : {len(rows)}  （要求 ≥50）")
    print(f"  空 text 行          : {empty_text}  （要求 0）")
    print(f"  tags 混用 ; 或 ,    : {bad_tags}  （要求 0，统一用 |）")
    print(f"  author 为空         : {empty_author} 条（原站缺失，清洗时填「未知」）")
    print(f"  tags 为空           : {empty_tags} 条（原站缺失，清洗时填「无标签」）")
    ok = len(rows) >= 50 and empty_text == 0 and bad_tags == 0
    print(f"  验收结论            : {'通过' if ok else '未通过，请查看上面各项'}")
    print("[自检] " + "-" * 46)


def summary(stats, start):
    elapsed = time.time() - start
    print(f"\n[统计] 总请求数: {stats['requests']}  |  总耗时: {elapsed:.1f} 秒")
    if stats["failed_pages"]:
        print(f"[统计] 重试后仍失败并跳过的页码: {stats['failed_pages']}")


# ------------------------------------------------------------ 主流程
def main():
    parser = argparse.ArgumentParser(description="quotes.toscrape.com 合规采集脚本")
    parser.add_argument("--full", action="store_true",
                        help="放开翻页，采集前 5 页全量数据并写 CSV（默认只采首页前 5 条核对）")
    parser.add_argument("--pages", type=int, default=MAX_PAGES_HARD,
                        help=f"采集页数，默认 {MAX_PAGES_HARD}，上限锁定 {MAX_PAGES_HARD} 页")
    args = parser.parse_args()

    max_pages = min(max(1, args.pages), MAX_PAGES_HARD)
    stats = {"requests": 0, "failed_pages": []}
    rows = []
    start = time.time()

    print(f"[开始] {datetime.now():%Y-%m-%d %H:%M:%S}  模式: "
          f"{'全量 --full（最多 %d 页）' % max_pages if args.full else '试采（仅第 1 页前 5 条）'}")

    url = f"{BASE_URL}/page/1/"
    page = 1
    while url and page <= max_pages:
        print(f"[抓取] 第 {page} 页 → {url}")
        html = fetch(url, stats)

        if html is None:
            stats["failed_pages"].append(page)
            print(f"  [跳过] 第 {page} 页重试后仍失败，已记录并跳过")
        else:
            page_rows = parse_page(html, page)
            rows.extend(page_rows)
            print(f"  [成功] 本页 {len(page_rows)} 条，累计 {len(rows)} 条")

            if not args.full:          # 试采模式：采完第 1 页就停
                break
            url = next_page_url(html)

        page += 1

    # ---- 试采模式：打印前 5 条供人工核对，不写文件
    if not args.full:
        print(f"\n[人工核对] 首页前 {min(5, len(rows))} 条：")
        print_table(rows[:5])
        print("\n[字段清单] " + "  /  ".join(FIELDS))
        print("[下一步] 核对 author / author_url / tags 无误后，加 --full 正式采集前 5 页。")
        summary(stats, start)
        return

    # ---- 全量模式：自检 → 写文件
    self_check(rows)
    if rows:
        fname = save_csv(rows)
        print(f"\n[保存] {fname}（编码 utf-8-sig，{len(rows)} 条）")
    else:
        print("\n[保存] 未采集到数据，未生成文件")
    summary(stats, start)


if __name__ == "__main__":
    main()
