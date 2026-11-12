# -*- coding: utf-8 -*-
"""课内必做 5 项验收自检：逐项核对并生成 VERIFY.md。"""
import csv
import glob
import os
import re

WS = r"D:\deepseekworkspace"
os.chdir(WS)

results = []


def add(name, ok, detail):
    results.append((name, ok, detail))


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ---------- 定位文件
raw_csv = sorted(glob.glob("data_quotes_*.csv"))
raw_csv = [f for f in raw_csv if "clean" not in f]
clean_csv = sorted(glob.glob("data_quotes_clean_*.csv"))
raw_csv = max(raw_csv, key=os.path.getmtime) if raw_csv else None
clean_csv = max(clean_csv, key=os.path.getmtime) if clean_csv else None

rows_raw = read_rows(raw_csv) if raw_csv else []
rows_clean = read_rows(clean_csv) if clean_csv else []

# ---------- ① 条数与字段
FIELDS = ["text", "author", "author_url", "tags", "page"]
field_ok = all(list(r.keys()) == FIELDS for r in rows_raw) if rows_raw else False
empty = {f: sum(1 for r in rows_raw if not str(r[f]).strip()) for f in FIELDS} if rows_raw else {}
add("① ≥50 条 + 每条 ≥5 字段",
    len(rows_raw) >= 50 and field_ok and empty.get("text", 1) == 0,
    f"条数={len(rows_raw)}，字段={list(rows_raw[0].keys()) if rows_raw else '无'}，"
    f"空值统计={empty}")

# ---------- ② 清洗日志四项齐全
log_txt = open("clean_log.txt", encoding="utf-8").read() if os.path.exists("clean_log.txt") else ""
need = {
    "去重": "① 去重" in log_txt and "重复条数" in log_txt,
    "补空": "② 补空" in log_txt and "「未知」" in log_txt and "「无标签」" in log_txt,
    "统一格式": "③ 统一格式" in log_txt,
    "极值校验": "④ 极值校验" in log_txt and "非空率" in log_txt and "min" in log_txt,
    "行数前后对比": "处理前行数" in log_txt and "处理行后数" in log_txt,
}
add("② 清洗日志四项齐全 (+每步行数)",
    all(need.values()),
    "；".join(f"{k}={'有' if v else '缺'}" for k, v in need.items()))

# ---------- ③ utf-8-sig / Excel 无乱码
boms = {}
for p in (raw_csv, clean_csv):
    if p:
        boms[p] = open(p, "rb").read(3) == b"\xef\xbb\xbf"
add("③ CSV utf-8-sig（Excel 无乱码）",
    all(boms.values()) and len(boms) == 2,
    "；".join(f"{k}: BOM={'有' if v else '无'}" for k, v in boms.items()))

# ---------- ④ sleep + 总请求数
crawler_src = open("crawler.py", encoding="utf-8").read()
m_sleep = re.search(r"SLEEP_SEC\s*=\s*([\d.]+)", crawler_src)
sleep_val = float(m_sleep.group(1)) if m_sleep else 0
has_req = "总请求数" in crawler_src
has_time = "总耗时" in crawler_src
add("④ sleep(≥1 秒) + 打印总请求数",
    sleep_val >= 1 and has_req and has_time,
    f"SLEEP_SEC={sleep_val}，打印总请求数={'有' if has_req else '无'}，打印总耗时={'有' if has_time else '无'}")

# ---------- ⑤ robots 证据
rob_txt = os.path.exists("robots_evidence.txt")
rob_png = os.path.exists("robots_evidence.png") or os.path.exists("robots_evidence_annotated.png")
rob_log = "HTTP 404" in open("robots_evidence.txt", encoding="utf-8").read() if rob_txt else False
add("⑤ robots.txt 检查在案",
    rob_txt and rob_png,
    f"记录文件={'有' if rob_txt else '无'}，截图={'有' if rob_png else '无'}，"
    f"实测状态={'HTTP 404（站点无 robots.txt，按 RFC 9309 未声明限制）' if rob_log else '未知'}")

# ---------- 汇总
passed = sum(1 for _, ok, _ in results if ok)
lines = ["# 课内必做 5 项验收报告", "",
         f"生成时间：2026-11-06  |  通过：**{passed}/{len(results)}**", "",
         "| # | 验收项 | 结果 | 证据 |", "|---|---|---|---|"]
for i, (name, ok, detail) in enumerate(results, 1):
    lines.append(f"| {i} | {name} | {'✅ 通过' if ok else '❌ 未通过'} | {detail} |")

lines += ["", "## 数据文件", "",
          f"- 原始：`{raw_csv}`（{len(rows_raw)} 条）",
          f"- 清洗后：`{clean_csv}`（{len(rows_clean)} 条）",
          "", "## 数据样本（清洗后前 5 条）", "",
          "| # | author | text | tags | page |", "|---|---|---|---|---|"]
for i, r in enumerate(rows_clean[:5], 1):
    text = r["text"][:60].replace("|", "\\|")
    lines.append(f"| {i} | {r['author']} | {text}… | {r['tags']} | {r['page']} |")

open("VERIFY.md", "w", encoding="utf-8").write("\n".join(lines) + "\n")

for name, ok, detail in results:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    print(f"        {detail}")
print()
print(f"通过 {passed}/{len(results)}  →  VERIFY.md 已生成")
