# -*- coding: utf-8 -*-
"""第二验证：用 pandas 之外的方法重算关键数字，与 pandas 结果对照。"""
import csv
import statistics
from collections import Counter

import pandas as pd

PATH = "data_quotes_clean_20261106.csv"
df = pd.read_csv(PATH, encoding="utf-8-sig")
rows = list(csv.DictReader(open(PATH, encoding="utf-8-sig")))

print("=" * 66)
print(f"{'指标':<22}{'pandas':>12}{'第二方法':>12}{'一致?':>8}")
print("-" * 66)


def check(name, a, b):
    ok = "一致" if a == b else "不一致"
    print(f"{name:<22}{str(a):>12}{str(b):>12}{ok:>8}")


# 1) 总条数
a = len(df)
b = len(rows)
check("总条数", a, b)

# 2) Einstein 条数（值计数 vs 逐行过滤）
a = int((df["author"] == "Albert Einstein").sum())
b = sum(1 for r in rows if r["author"].strip() == "Albert Einstein")
check("Einstein 条数", a, b)

# 3) Top5 合计（value_counts vs Counter.most_common）
vc = df["author"].value_counts()
a = int(vc.head(5).sum())
cnt = Counter(r["author"].strip() for r in rows)
b = sum(n for _, n in cnt.most_common(5))
check("Top5 合计", a, b)

# 4) 标签总数（explode vs 逐行 split 累加）
tags = df["tags"].str.split("|").explode().str.strip()
a = int((tags != "").sum())
b = sum(len([t for t in r["tags"].split("|") if t.strip()]) for r in rows)
check("标签总数", a, b)

# 5) 不同标签数
a = int(tags[tags != ""].nunique())
b = len({t for r in rows for t in r["tags"].split("|") if t.strip()})
check("不同标签数", a, b)

# 6) 文本长度中位数
a = float(df["text"].str.len().median())
b = float(statistics.median(len(r["text"]) for r in rows))
check("长度中位数", a, b)

# 7) 作者总数
a = int(df["author"].nunique())
b = len(cnt)
check("作者总数", a, b)

print("=" * 66)
print("\nTop5 明细（Counter 结果）：")
for name, n in cnt.most_common(5):
    print(f"  {name:<20} {n} 条")

print("\n标签 Top5（第二方法）：")
tag_cnt = Counter(t for r in rows for t in r["tags"].split("|") if t.strip())
for name, n in tag_cnt.most_common(5):
    print(f"  {name:<20} {n} 次")
