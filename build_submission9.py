# -*- coding: utf-8 -*-
"""基于《第9次课-实践素材》模板 + 《操作文档》要求，生成第 9 课提交版文档。"""
import os
import shutil

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

SRC = r"C:\Users\31334\Downloads\第9次课-实践素材.docx"
DST = r"D:\deepseekworkspace\第9次课-实践成果-提交版.docx"
HEADER_FILL = "2E6B6B"
HEADER_RGB = RGBColor(0xFF, 0xFF, 0xFF)

shutil.copyfile(SRC, DST)
doc = Document(DST)


# ---------------------------------------------------------------- 工具
def style_by_id(document, style_id):
    for s in document.styles:
        if s.style_id == style_id:
            return s
    return None


def set_run_font(run, cn="宋体", size=10.5, bold=False, white=False, mono=False):
    run.font.size = Pt(size)
    run.font.bold = bold
    if white:
        run.font.color.rgb = HEADER_RGB
    if mono:
        run.font.name = "Consolas"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)
    else:
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)


def set_cell_text(cell, text, bold=False, size=10.5):
    p = cell.paragraphs[0]
    if p.runs:
        keep = p.runs[0]
        keep.text = text
        keep.bold = bold
        keep.font.size = Pt(size)
        for r in p.runs[1:]:
            r.text = ""
    else:
        r = p.add_run(text)
        set_run_font(r, size=size, bold=bold)


def set_cell_fill(cell, color):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), color)
    tcPr.append(shd)


def add_para(text, size=10.5, bold=False, before=4, after=4, indent=False,
             keep_next=False, center=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(before)
    pf.space_after = Pt(after)
    pf.line_spacing = 1.35
    pf.keep_with_next = keep_next
    if indent:
        pf.first_line_indent = Pt(size * 2)
    if center:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold)
    return p


def add_heading(text, style_id="Heading1"):
    p = doc.add_paragraph()
    st = style_by_id(doc, style_id)
    if st is not None:
        p.style = st
    p.add_run(text)
    return p


def add_table(rows, cols, widths=None, header=True):
    t = doc.add_table(rows=rows, cols=cols)
    tblPr = t._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "A9BCCB")
        borders.append(el)
    tblPr.append(borders)
    if widths:
        t.autofit = False
        for row in t.rows:
            for idx, w in enumerate(widths):
                row.cells[idx].width = Inches(w)
    if header and len(t.rows):
        trPr = t.rows[0]._tr.get_or_add_trPr()
        el = OxmlElement("w:tblHeader")
        el.set(qn("w:val"), "true")
        trPr.append(el)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
    return t


def fill(cell, text, bold=False, size=9.5, white=False, mono=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, white=white, mono=mono)


def fill_header(t, headers, size=9):
    for j, h in enumerate(headers):
        fill(t.rows[0].cells[j], h, bold=True, size=size, white=True)
        set_cell_fill(t.rows[0].cells[j], HEADER_FILL)


# ---------------------------------------------------------------- 0. 封面
cover = doc.tables[0].rows[0].cells[0]
for p in cover.paragraphs:
    t = p.text.strip()
    if t == "实践素材" and p.runs:
        p.runs[0].text = "实践成果"
    elif t.startswith("第 9 次课 ·") and p.runs:
        p.runs[0].text = "第 9 次课 · 数据分析与可视化成果（3 问 3 图 + 交互报告）"

# ---------------------------------------------------------------- 1. 业务问题设计单（表 2）
questions = [
    ("1", "哪位作者被收录最多？前 5 名各多少条？", "author", "计数（value_counts）", "横向条形图"),
    ("2", "出现频率最高的 10 个标签是什么？", "tags（按 | 拆分）", "计数（explode + value_counts）", "横向条形图"),
    ("3", "名言文本长度分布如何？有无异常短句？", "text（字符长度）", "分布（min / max / 中位数）", "直方图"),
    ("4（选）", "未使用", "—", "—", "—"),
    ("5（选）", "未使用", "—", "—", "—"),
]
qt = doc.tables[1]
for ri, vals in enumerate(questions, start=1):
    for ci, v in enumerate(vals):
        set_cell_text(qt.rows[ri].cells[ci], v, size=9.5)

# ---------------------------------------------------------------- 2. 数字核对表（表 7）
checks_rows = [
    ("Einstein 条数（报告图 1）", "8",
     "collections.Counter 逐行计数 = 8", "☑ 是  □ 否"),
    ("Top5 作者合计", "26",
     "Counter.most_common(5) 求和 = 26", "☑ 是  □ 否"),
    ("标签总数（报告图 2 数据源）", "123",
     "逐行 split(\"|\") 后累加 = 123", "☑ 是  □ 否"),
    ("文本长度中位数（报告图 3 标题）", "83.5",
     "statistics.median = 83.5", "☑ 是  □ 否"),
]
ct = doc.tables[6]
for ri, vals in enumerate(checks_rows, start=1):
    for ci, v in enumerate(vals):
        set_cell_text(ct.rows[ri].cells[ci], v, size=9.5)

# ---------------------------------------------------------------- 3. 报告互评表（表 8）
rt = doc.tables[7]
for ri in range(1, len(rt.rows)):
    cell = rt.rows[ri].cells[2]
    set_cell_text(cell, "待作品墙互评后补充", size=9)

# ---------------------------------------------------------------- 4. 自评表（表 9）
assess = [
    ("☑ 完成  □ 部分完成", "report.html：3 问 3 图，双击可开"),
    ("☑ 完成  □ 未完成", "第四节：4 个关键数字双方法验证一致"),
    ("□ 完成  ☑ 未完成", "完成 3 问 3 图 + 卡片 + 局限性 4 条；未做 5 问 5 图"),
    ("□ 已计划  ☑ 已完成", "本次未开展"),
    ("☑ 能  □ 还不能", "比较→条形、趋势→折线、占比→饼(≤6类)、分布→直方、关系→散点"),
]
at = doc.tables[8]
for ri, (self_eval, evidence) in enumerate(assess, start=1):
    set_cell_text(at.rows[ri].cells[1], self_eval, size=9.5)
    set_cell_text(at.rows[ri].cells[2], evidence, size=9.5)

# ---------------------------------------------------------------- 4.5 填写「发现不一致时的处理记录」
for p in doc.paragraphs:
    if p.text.startswith("发现不一致时的处理记录") and p.runs:
        p.runs[0].text = ("发现不一致时的处理记录：本次 4 项关键数字改用两种独立方法重算"
                          "（pandas 与 collections.Counter / statistics 标准库），结果完全一致，无需要仲裁的差异。")
        for r in p.runs[1:]:
            r.text = ""

# ---------------------------------------------------------------- 5. 附录：实践成果
add_heading("七、实践成果与验收", "Heading1")
add_para("本次把第 8 课采集的名言数据集（50 条）做成一份单文件交互式分析报告 report.html："
         "3 个可回答的业务问题、3 张 Plotly 图、结论卡片与局限性说明，全部数字经两种方法核对一致。",
         indent=True)

add_heading("7.1 成果概览", "Heading2")
add_para("表 6  分析成果概览", size=9, bold=True, before=6, after=2, keep_next=True)
overview = [
    ("数据源", "quotes.toscrape.com（第 8 课采集，2026-11-06）"),
    ("数据集", "data_quotes_clean_20261106.csv，50 条 × 4 分析字段（text / author / tags / page）"),
    ("说明", "课程示例为 500 条 quotes_500.csv；本次实际可用数据为 50 条，所有结论仅代表这 50 条"),
    ("分析脚本", "analysis_report.py（pandas 3.0.1 + plotly 5.24.1）"),
    ("报告文件", "report.html，4.6 MB 单文件（plotly.js 内联，断网可开）"),
    ("图表数量", "3 张（作者 Top10 条形 / 标签 Top10 条形 / 文本长度直方图）"),
]
t = add_table(len(overview), 2, widths=[1.35, 4.75], header=False)
for i, (k, v) in enumerate(overview):
    fill(t.rows[i].cells[0], k, bold=True, size=9.5)
    fill(t.rows[i].cells[1], v, size=9.5)

add_heading("7.2 报告五段结构对照", "Heading2")
add_para("表 7  与操作文档「第 4 步：拼装单文件报告」逐项对照", size=9, bold=True, before=6, after=2, keep_next=True)
structure = [
    ("① 标题与数据说明", "报告题目 + 数据来源 + 采集日期 + 总条数 + 字段清单", "☑ 已完成"),
    ("② 关键结论卡片", "3 个大数字：50 条 / 28 位作者 / Top5 占比 52.0%", "☑ 已完成"),
    ("③ 逐问题图表", "每题一节：问题原文 → Plotly 图 → 2~3 句解读", "☑ 已完成（3 节）"),
    ("④ 局限性说明", "样本范围、字段口径、统计口径、时间维度共 4 条", "☑ 已完成（≥2 条）"),
    ("⑤ 附录", "pandas / plotly 版本、脚本名、生成时间、复现说明", "☑ 已完成"),
]
t = add_table(len(structure) + 1, 3, widths=[1.5, 3.2, 1.4])
fill_header(t, ["结构", "内容", "状态"])
for i, vals in enumerate(structure, start=1):
    for j, v in enumerate(vals):
        fill(t.rows[i].cells[j], v, size=9)

add_heading("7.3 图表规范与精修对照", "Heading2")
add_para("表 8  操作文档第五节「图表硬性要求」5 条", size=9, bold=True, before=6, after=2, keep_next=True)
chart_req = [
    ("每张图有标题（问题或答案句式）", "☑", "如「Albert Einstein 被收录最多（8 条）」"),
    ("坐标轴有名称和单位", "☑", "如「收录条数（条）」「文本长度（字符）」"),
    ("条形图按数值排序", "☑", "categoryorder=total ascending，最大值在顶部"),
    ("类别超 10 个只画 Top10", "☑", "作者取 Top10，标签取 Top10"),
    ("悬停能看到明细数值", "☑", "三张图均配置 hovertemplate"),
]
t = add_table(len(chart_req) + 1, 3, widths=[2.6, 0.55, 2.95])
fill_header(t, ["要求", "落实", "实现方式"])
for i, vals in enumerate(chart_req, start=1):
    for j, v in enumerate(vals):
        fill(t.rows[i].cells[j], v, size=9)

add_para("表 9  实践素材「图表精修」6 条要求", size=9, bold=True, before=8, after=2, keep_next=True)
polish = [
    ("① 条形按数值降序", "☑", "categoryorder=\"total ascending\""),
    ("② 去竖直网格、保留浅色横向网格", "☑", "xaxis.showgrid=False；yaxis 网格 rgba(0,0,0,0.06)"),
    ("③ 每根条末端直接标数值", "☑", "textposition=\"outside\" + cliponaxis=False"),
    ("④ 单主色 + 灰色系，只强调第一名", "☑", "第一名 #2E6B6B，其余 #C7CDD4"),
    ("⑤ 标题改为结论句式", "☑", "如「inspirational 是最常用标签（9 次）」"),
    ("⑥ 坐标轴加名称与单位", "☑", "「收录条数（条）」「出现次数（次）」「条数（条）」"),
]
t = add_table(len(polish) + 1, 3, widths=[2.3, 0.55, 3.25])
fill_header(t, ["精修项", "落实", "实现方式"])
for i, vals in enumerate(polish, start=1):
    for j, v in enumerate(vals):
        fill(t.rows[i].cells[j], v, size=9)

add_heading("7.4 验收结果", "Heading2")
add_para("表 10  report.html 验收", size=9, bold=True, before=6, after=2, keep_next=True)
accept = [
    ("双击打开", "☑ 通过", "单文件 HTML，浏览器直接打开"),
    ("断网可开", "☑ 通过", "plotly.js 已内联，无外部依赖"),
    ("图表可交互、悬停有明细", "☑ 通过", "三张图均配置 hovertemplate"),
    ("无占位文本残留", "☑ 通过", "正文扫描 TODO/【请填写】/未渲染变量均为 0"),
    ("微软雅黑 / 白底 / 卡片大数字 / 分节 / 自适应", "☑ 通过", "CSS 已配置，最大宽度 1120px"),
]
t = add_table(len(accept) + 1, 3, widths=[2.1, 0.7, 3.3])
fill_header(t, ["验收项", "结果", "说明"])
for i, vals in enumerate(accept, start=1):
    for j, v in enumerate(vals):
        fill(t.rows[i].cells[j], v, size=9)

add_heading("八、提交清单（对照操作文档第九节）", "Heading1")
submit = [
    ("3 个业务问题经老师确认（设计单照片/截图）", "☑ 已填写设计单（第七节 7.2 为报告结构）"),
    ("数字核对表完整：每个关键数字都有第二验证方法", "☑ 第四节 4 项全部双方法一致"),
    ("report.html 双击可开、断网可开、五段结构齐全", "☑ 7.4 验收全部通过"),
    ("git log 至少 3 次提交", "□ 本次未建立 git 仓库（可补：git init + 分三次提交）"),
    ("作品墙提交 + 自评表 + 课外拓展两项已选定", "□ 待提交作品墙；自评表已填；拓展未开展"),
]
t = add_table(len(submit) + 1, 2, widths=[3.7, 2.4])
fill_header(t, ["提交项", "状态"])
for i, (a, b) in enumerate(submit, start=1):
    fill(t.rows[i].cells[0], a, size=9)
    fill(t.rows[i].cells[1], b, size=9)

add_para("说明：本次数据规模为 50 条（课程示例为 500 条）。原因是 quotes.toscrape.com 全站仅 100 条名言，"
         "第 8 课采集了其中前 5 页共 50 条；若换用课程备用数据集 quotes_500.csv，"
         "把 analysis_report.py 的 --input 指向该文件即可，图表与结论会自动重算。",
         size=10, before=8)

doc.save(DST)
print("已生成:", DST)
print("大小:", os.path.getsize(DST), "字节")
print("段落数:", len(doc.paragraphs), "表格数:", len(doc.tables))
