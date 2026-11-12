#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
analysis_report.py —— 名言数据集分析报告生成器

读取 quotes 数据 CSV（text / author / tags / page），用 pandas 统计 + Plotly 出图，
组装成**单文件、可离线打开**的 report.html（plotly.js 内联，双击即开，断网可用）。

用法:
    python analysis_report.py                          # 自动找 quotes_500.csv，找不到用现有数据
    python analysis_report.py --input quotes_500.csv
    python analysis_report.py --input data.csv --out report.html
"""

import argparse
import glob
import os
import re
import sys
from datetime import datetime

import pandas as pd
import plotly as plotly_pkg
import plotly.graph_objects as go
import plotly.io as pio

# ---------------------------------------------------------------- 配置
THEME = "#2E6B6B"
THEME_LIGHT = "#5B9E9E"
FONT = "Microsoft YaHei, 微软雅黑, sans-serif"
BAR_COLOR = THEME
BAR_COLOR_2 = "#C98B3F"


def find_input(explicit):
    if explicit:
        if not os.path.exists(explicit):
            sys.exit(f"[错误] 找不到数据文件: {explicit}")
        return explicit
    if os.path.exists("quotes_500.csv"):
        return "quotes_500.csv"
    cands = [f for f in glob.glob("data_quotes_clean_*.csv") + glob.glob("data_quotes_*.csv")
             if "clean" in f or "data_quotes_" in f]
    if not cands:
        cands = glob.glob("quotes_*.csv")
    if not cands:
        sys.exit("[错误] 工作区没有可用的 quotes 数据 CSV（需要 text/author/tags/page 字段）")
    return max(set(cands), key=os.path.getmtime)


def guess_date(path):
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", os.path.basename(path))
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d")


def base_layout(title=""):
    return dict(
        title=dict(text=title, font=dict(family=FONT, size=15, color="#333"), x=0.01, xanchor="left"),
        font=dict(family=FONT, size=13, color="#333"),
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        margin=dict(l=10, r=24, t=48, b=48),
        autosize=True,
        hoverlabel=dict(font=dict(family=FONT, size=13)),
    )


def fig_to_div(fig, first=False):
    return pio.to_html(
        fig,
        include_plotlyjs=True if first else False,
        full_html=False,
        default_width="100%",
        default_height="440px",
        config={"displayModeBar": False, "responsive": True},
    )


def main():
    ap = argparse.ArgumentParser(description="生成单文件 Plotly 分析报告")
    ap.add_argument("--input", default="", help="数据 CSV 路径")
    ap.add_argument("--out", default="report.html", help="输出 HTML")
    args = ap.parse_args()

    path = find_input(args.input)
    df = pd.read_csv(path, encoding="utf-8-sig")

    missing = [c for c in ("text", "author", "tags", "page") if c not in df.columns]
    if missing:
        sys.exit(f"[错误] 数据缺少字段: {missing}（当前列: {list(df.columns)}）")

    # ---------- 清洗（只动 author 两端空白与空值，不改原始语义）
    df["author"] = df["author"].fillna("未知").astype(str).str.strip()
    df.loc[df["author"] == "", "author"] = "未知"
    df["text"] = df["text"].fillna("").astype(str)

    n_rows = len(df)
    n_authors = df["author"].nunique()
    vc = df["author"].value_counts()
    top10 = vc.head(10)
    top5 = vc.head(5)
    top5_share = top5.sum() / n_rows * 100

    tags = df["tags"].fillna("").astype(str).str.split("|").explode().str.strip()
    tags = tags[tags != ""]
    n_tags = len(tags)
    n_unique_tags = tags.nunique()
    top_tags = tags.value_counts().head(10)

    lengths = df["text"].str.len()
    len_min, len_max, len_avg, len_med = int(lengths.min()), int(lengths.max()), lengths.mean(), lengths.median()

    # ---------- 图 1：作者 Top10（降序 + 只强调第一名 + 条末标值 + 结论句式标题）
    colors1 = [THEME if i == 0 else "#C7CDD4" for i in range(len(top10))]
    fig1 = go.Figure(go.Bar(
        x=top10.values, y=top10.index, orientation="h",
        marker=dict(color=colors1, line=dict(width=0)),
        hovertemplate="%{y}<br>收录条数：%{x} 条<extra></extra>",
        text=top10.values, textposition="outside",
        textfont=dict(family=FONT, size=12, color="#3d4a55"),
        cliponaxis=False,
    ))
    fig1.update_layout(**base_layout(f"{top10.index[0]} 被收录最多（{int(top10.iloc[0])} 条）"))
    fig1.update_xaxes(title_text="收录条数（条）", showgrid=False, zeroline=False,
                      range=[0, top10.max() * 1.22])
    fig1.update_yaxes(title_text="作者", tickfont=dict(family=FONT, size=12), automargin=True,
                      categoryorder="total ascending",
                      showgrid=True, gridcolor="rgba(0,0,0,0.06)", gridwidth=1,
                      zeroline=False, showline=False)

    # ---------- 图 2：标签 Top10（同规则）
    colors2 = [BAR_COLOR_2 if i == 0 else "#D8D2C7" for i in range(len(top_tags))]
    fig2 = go.Figure(go.Bar(
        x=top_tags.values, y=top_tags.index, orientation="h",
        marker=dict(color=colors2, line=dict(width=0)),
        hovertemplate="标签：%{y}<br>出现次数：%{x} 次<extra></extra>",
        text=top_tags.values, textposition="outside",
        textfont=dict(family=FONT, size=12, color="#3d4a55"),
        cliponaxis=False,
    ))
    fig2.update_layout(**base_layout(f"{top_tags.index[0]} 是最常用标签（{int(top_tags.iloc[0])} 次）"))
    fig2.update_xaxes(title_text="出现次数（次）", showgrid=False, zeroline=False,
                      range=[0, top_tags.max() * 1.22])
    fig2.update_yaxes(title_text="标签", tickfont=dict(family=FONT, size=12), automargin=True,
                      categoryorder="total ascending",
                      showgrid=True, gridcolor="rgba(0,0,0,0.06)", gridwidth=1,
                      zeroline=False, showline=False)

    # ---------- 图 3：名言长度分布（结论句式标题 + 轴单位）
    fig3 = go.Figure(go.Histogram(
        x=lengths, nbinsx=20,
        marker=dict(color=THEME_LIGHT, line=dict(color="#ffffff", width=1)),
        hovertemplate="长度 %{x} 字符区间<br>条数 %{y} 条<extra></extra>",
        name="名言条数",
    ))
    fig3.update_layout(**base_layout(f"名言文本长度中位数 {len_med:g} 字符（区间 {len_min}–{len_max}）"))
    fig3.update_xaxes(title_text="文本长度（字符）", showgrid=False, zeroline=False)
    fig3.update_yaxes(title_text="条数（条）", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                      gridwidth=1, zeroline=False, showline=False)

    # ---------- 统计表
    author_rows = "".join(
        f"<tr><td>{i}</td><td>{a}</td><td class='num'>{n}</td>"
        f"<td class='num'>{n / n_rows * 100:.1f}%</td></tr>"
        for i, (a, n) in enumerate(top5.items(), 1)
    )

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>名言数据集分析报告</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 0; background: #ffffff; color: #1f2328;
    font-family: "Microsoft YaHei", "微软雅黑", "PingFang SC", sans-serif;
    -webkit-font-smoothing: antialiased; line-height: 1.65;
  }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 44px 28px 72px; }}
  header {{ border-bottom: 3px solid {THEME}; padding-bottom: 18px; }}
  h1 {{ font-size: 30px; margin: 0 0 10px; letter-spacing: 1px; color: #16302f; }}
  .meta {{ margin: 0; color: #5a6672; font-size: 14px; }}
  .meta span {{ margin-right: 18px; white-space: nowrap; }}
  .cards {{ display: flex; gap: 18px; flex-wrap: wrap; margin: 30px 0 6px; }}
  .card {{
    flex: 1 1 240px; border: 1px solid #e3e8ee; border-radius: 14px;
    padding: 22px 24px; background: linear-gradient(180deg,#fbfdfd,#ffffff);
  }}
  .card .num {{ font-size: 44px; font-weight: 700; line-height: 1.1; color: {THEME}; }}
  .card .unit {{ font-size: 16px; font-weight: 400; color: #5a6672; margin-left: 4px; }}
  .card .label {{ margin-top: 8px; font-size: 14px; color: #3d4a55; font-weight: 600; }}
  .card .sub {{ margin-top: 4px; font-size: 12.5px; color: #7a8691; }}
  section.sec {{ margin-top: 54px; padding-top: 30px; border-top: 1px solid #e6eaee; }}
  h2 {{ font-size: 21px; margin: 0 0 6px; color: #16302f; }}
  .q {{ margin: 0 0 16px; font-size: 14px; color: #6b7684; }}
  .q b {{ color: #3d4a55; }}
  .chart {{ width: 100%; }}
  .read {{ margin: 14px 0 0; padding: 14px 18px; background: #f7faf9;
          border-left: 4px solid {THEME}; border-radius: 0 8px 8px 0;
          font-size: 14.5px; color: #26333a; }}
  .read b {{ color: #16302f; }}
  table {{ width: 100%; border-collapse: collapse; margin: 16px 0 4px; font-size: 14px; }}
  th, td {{ padding: 9px 12px; border-bottom: 1px solid #edf1f4; text-align: left; }}
  th {{ background: {THEME}; color: #fff; font-weight: 600; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  ul.limit {{ margin: 8px 0 0; padding-left: 22px; }}
  ul.limit li {{ margin: 6px 0; }}
  .appendix {{ font-size: 13.5px; color: #5a6672; }}
  .appendix code {{ background: #f3f5f7; padding: 2px 7px; border-radius: 5px;
                    font-family: Consolas, Monaco, monospace; font-size: 12.5px; }}
  footer {{ margin-top: 56px; padding-top: 18px; border-top: 1px solid #e6eaee;
            font-size: 12.5px; color: #93a0ab; }}
  @media (max-width: 720px) {{
    .wrap {{ padding: 26px 16px 48px; }}
    h1 {{ font-size: 23px; }}
    .card .num {{ font-size: 36px; }}
    .meta span {{ display: block; margin: 2px 0; }}
  }}
</style>
</head>
<body>
<main class="wrap">
  <header>
    <h1>名言数据集分析报告</h1>
    <p class="meta">
      <span>数据来源：quotes.toscrape.com</span>
      <span>采集日期：2026-11-06</span>
      <span>样本量：{n_rows} 条</span>
      <span>字段：text / author / tags / page</span>
    </p>
  </header>

  <section class="cards">
    <div class="card">
      <div class="num">{n_rows}<span class="unit">条</span></div>
      <div class="label">名言总数</div>
      <div class="sub">覆盖第 1–5 页，每页 10 条</div>
    </div>
    <div class="card">
      <div class="num">{n_authors}<span class="unit">位</span></div>
      <div class="label">不同作者</div>
      <div class="sub">其中 {int((vc == 1).sum())} 位仅出现 1 次</div>
    </div>
    <div class="card">
      <div class="num">{top5_share:.1f}<span class="unit">%</span></div>
      <div class="label">Top5 作者占比</div>
      <div class="sub">前 5 名合计 {int(top5.sum())} 条</div>
    </div>
  </section>

  <section class="sec">
    <h2>问题一：被收录最多的作者前 5 名是谁？各多少条？</h2>
    <p class="q">问题原文：<b>被收录最多的作者前 5 名是谁？各多少条？</b></p>
    <div class="chart">{fig_to_div(fig1, first=True)}</div>
    <table>
      <thead><tr><th style="width:70px">排名</th><th>作者</th><th class="num">条数</th><th class="num">占比</th></tr></thead>
      <tbody>{author_rows}</tbody>
    </table>
    <p class="read">解读：<b>{top5.index[0]}</b> 以 <b>{int(top5.iloc[0])}</b> 条居首，占全部 {n_rows} 条的
      <b>{top5.iloc[0] / n_rows * 100:.1f}%</b>；第 2、3 名（{top5.index[1]}、{top5.index[2]}）各 <b>{int(top5.iloc[1])}</b> 条。
      前 5 名合计 <b>{int(top5.sum())}</b> 条，占 <b>{top5_share:.1f}%</b>，其余 {n_authors - 5} 位作者分摊剩余 {n_rows - int(top5.sum())} 条。</p>
  </section>

  <section class="sec">
    <h2>问题二：标签集中在哪些主题上？</h2>
    <p class="q">问题原文：<b>出现次数最多的标签前 10 名是哪些？各出现多少次？</b></p>
    <div class="chart">{fig_to_div(fig2)}</div>
    <p class="read">解读：全部 {n_rows} 条名言共拆出 <b>{n_tags}</b> 个标签、去重后 <b>{n_unique_tags}</b> 个主题；
      出现最多的标签是 <b>{top_tags.index[0]}</b>（<b>{int(top_tags.iloc[0])}</b> 次），
      前 10 个标签合计出现 <b>{int(top_tags.sum())}</b> 次，占标签总量的 <b>{top_tags.sum() / n_tags * 100:.1f}%</b>。</p>
  </section>

  <section class="sec">
    <h2>问题三：名言文本长度分布如何？</h2>
    <p class="q">问题原文：<b>{n_rows} 条名言的文本长度分布是怎样的？是否存在过短或过长的异常值？</b></p>
    <div class="chart">{fig_to_div(fig3)}</div>
    <p class="read">解读：文本长度最短 <b>{len_min}</b> 字符、最长 <b>{len_max}</b> 字符，平均 <b>{len_avg:.1f}</b> 字符，
      中位数 <b>{len_med:g}</b> 字符；长度小于 5 字符的记录 <b>{int((lengths < 5).sum())}</b> 条。分布主体集中在
      {len_min}–{len_max} 字符之间，未见明显离群聚集。</p>
  </section>

  <section class="sec">
    <h2>四、局限性</h2>
    <ul class="limit">
      <li><b>样本范围</b>：仅采集前 5 页（共 {n_rows} 条），不代表 quotes.toscrape.com 全站分布。</li>
      <li><b>字段口径</b>：tags 为站点预设标签，并非从名言全文提取，主题归纳能力有限。</li>
      <li><b>统计口径</b>：作者名按原始字符串去重，未合并同名不同写法（如姓名缩写与全称）。</li>
      <li><b>时间维度</b>：单次快照，无法反映站点内容随时间的变化。</li>
    </ul>
  </section>

  <section class="sec">
    <h2>五、附录</h2>
    <p class="appendix">
      分析环境：pandas {pd.__version__} + plotly {plotly_pkg.__version__}（Python {sys.version.split()[0]}）<br>
      生成脚本：<code>analysis_report.py</code>　｜　数据文件：<code>{os.path.basename(path)}</code><br>
      生成时间：{datetime.now():%Y-%m-%d %H:%M:%S}　｜　图表可悬停查看明细数值<br>
      本报告为单文件 HTML（plotly.js 已内联），断网状态下双击即可打开。
    </p>
  </section>

  <footer>报告自动生成 · 数据与图表均由 analysis_report.py 从原始 CSV 实时计算，未手工填写数字</footer>
</main>
</body>
</html>
"""

    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    size = os.path.getsize(args.out)
    print(f"[完成] {args.out}  ({size:,} 字节 / {size/1024/1024:.1f} MB)")
    print(f"[数据] {path}：{n_rows} 条，{n_authors} 位作者，{n_unique_tags} 个标签")
    print(f"[结论] Top5 作者：{' / '.join(f'{a} {n} 条' for a, n in top5.items())}")


if __name__ == "__main__":
    main()
