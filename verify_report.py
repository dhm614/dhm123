# -*- coding: utf-8 -*-
"""检查 report.html 是否满足第 9 课图表硬性要求（先还原 JSON 里的 \\uXXXX 转义再查中文）。"""
import re

html = open("report.html", encoding="utf-8").read()


def unescape(s):
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)


text = unescape(html)

checks = {
    "图1 标题=结论句式（被收录最多）": "被收录最多（",
    "图2 标题=结论句式（最常用标签）": "是最常用标签（",
    "图3 标题=结论句式（中位数）": "文本长度中位数",
    "图1 x 轴：收录条数（条）": "收录条数（条）",
    "图2 x 轴：出现次数（次）": "出现次数（次）",
    "图3 x 轴：文本长度（字符）": "文本长度（字符）",
    "图3 y 轴：条数（条）": "条数（条）",
    "y 轴名称：作者": '"text":"作者"',
    "y 轴名称：标签": '"text":"标签"',
    "条形降序": "total ascending",
    "只强调第一名（灰）": "#C7CDD4",
    "条末标值": '"textposition":"outside"',
    "去除竖直网格": '"showgrid":false',
    "保留横向网格": '"gridcolor":"rgba(0,0,0,0.06)"',
    "悬停明细": "hovertemplate",
    "微软雅黑": "Microsoft YaHei",
}

print("=" * 64)
bad = 0
for name, needle in checks.items():
    ok = needle in text
    bad += 0 if ok else 1
    print(f"  {'✓' if ok else '✗'}  {name}")

print("=" * 64)
print(f"通过 {len(checks)-bad}/{len(checks)}")
print(f"文件字符数: {len(html):,} | 图表数: {html.count('class=\"plotly-graph-div\"')}")

# 中位数核对
m = re.search(r"文本长度中位数 ([0-9.]+) 字符", text)
print(f"图3 标题里的中位数: {m.group(1) if m else '未找到'}")
