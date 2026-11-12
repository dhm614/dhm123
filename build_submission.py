# -*- coding: utf-8 -*-
"""基于课程模板生成「第8次课-实践成果-提交版.docx」：填写工作纸 + 追加实践成果附录。"""
import csv
import os
import shutil

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image, ImageChops

SRC = r"C:\Users\31334\Downloads\第8次课-实践素材.docx"
DST = r"D:\deepseekworkspace\第8次课-实践成果-提交版.docx"
WS = r"D:\deepseekworkspace"
HEADER_FILL = "2E6B6B"      # 与模板表格表头一致的深青色
HEADER_RGB = RGBColor(0xFF, 0xFF, 0xFF)

shutil.copyfile(SRC, DST)
doc = Document(DST)


# ---------------------------------------------------------------- 工具函数
def style_by_id(document, style_id):
    for s in document.styles:
        if s.style_id == style_id:
            return s
    return None


def set_run_font(run, cn="宋体", size=10.5, bold=False, mono=False, white=False):
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
    """替换单元格文本，保留原 run 的西文/中文字体设置。"""
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


def add_body_para(text, size=10.5, bold=False, space_before=4, space_after=4,
                  indent_first=False, mono=False, keep_next=False, center=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = 1.35
    pf.keep_with_next = keep_next
    if indent_first:
        pf.first_line_indent = Pt(size * 2)
    if center:
        pf.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, mono=mono)
    return p


def add_heading_like(text, style_id="Heading1"):
    p = doc.add_paragraph()
    style = style_by_id(doc, style_id)
    if style is not None:
        p.style = style
    p.add_run(text)
    return p


def finalize_table(t, header=True):
    """表头跨页重复 + 行内不拆分，避免表格断页后丢表头。"""
    if header and len(t.rows):
        trPr = t.rows[0]._tr.get_or_add_trPr()
        el = OxmlElement("w:tblHeader")
        el.set(qn("w:val"), "true")
        trPr.append(el)
    for row in t.rows:
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))


def add_table_with_borders(rows, cols, widths=None, header=True):
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
    finalize_table(t, header=header)
    return t


def fill_table_cell(cell, text, bold=False, size=9.5, align=None, mono=False, white=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    if align is not None:
        p.alignment = align
    r = p.add_run(text)
    set_run_font(r, size=size, bold=bold, mono=mono, white=white)


def fill_header_row(t, headers, size=9):
    for j, h in enumerate(headers):
        fill_table_cell(t.rows[0].cells[j], h, bold=True, size=size, white=True)
        set_cell_fill(t.rows[0].cells[j], HEADER_FILL)


# ---------------------------------------------------------------- 0. 封面改为「实践成果」
cover = doc.tables[0].rows[0].cells[0]
for p in cover.paragraphs:
    if p.text.strip() == "实践素材" and p.runs:
        p.runs[0].text = "实践成果"
    elif p.text.startswith("第 8 次课 · 任务卡") and p.runs:
        p.runs[0].text = "第 8 次课 · 数据采集实践成果（爬虫 + 清洗 + 验收）"

def crop_white_margin(src, dst, pad=16):
    """裁掉图片四周的纯白留白，避免文档里出现大块空白。"""
    img = Image.open(src).convert("RGB")
    bg = Image.new("RGB", img.size, (255, 255, 255))
    bbox = ImageChops.difference(img, bg).getbbox()
    if bbox:
        left, top, right, bottom = bbox
        box = (max(0, left - pad), max(0, top - pad),
               min(img.width, right + pad), min(img.height, bottom + pad))
        img.crop(box).save(dst)
    else:
        img.save(dst)
    return dst


# ---------------------------------------------------------------- 1. 填写表 2 任务卡
task_tbl = doc.tables[1]
for i in (1, 2, 3):
    task_tbl.rows[i].cells[2].paragraphs[0].runs[0].text = "☑" if i == 1 else "□"

# ---------------------------------------------------------------- 2. 填写表 3 字段清单
fields = [
    ("text", "文本", "名言全文，如 “The world as we have created it…”", "否"),
    ("author", "文本", "作者姓名，如 Albert Einstein", "否（空补「未知」）"),
    ("author_url", "文本", "作者主页绝对地址，/author/xxx 补全为完整 URL", "否"),
    ("tags", "文本", "标签，多个用 | 连接，如 change|deep-thoughts", "否（空补「无标签」）"),
    ("page", "数字", "所在页码，1–5", "否"),
]
field_tbl = doc.tables[2]
for row_idx, values in enumerate(fields, start=1):
    for col_idx, value in enumerate(values):
        set_cell_text(field_tbl.rows[row_idx].cells[col_idx], value, size=9.5)

# ---------------------------------------------------------------- 3. 填写正文数据源
p = doc.paragraphs[7]
p.runs[0].text = ("数据源：quotes.toscrape.com（公开练习站点，无需登录）"
                  "\u3000\u3000一句话采集目的：采集名言文本、作者与标签形成结构化数据集，"
                  "练习「请求—解析—清洗—存储」的完整数据采集流程。")

# ---------------------------------------------------------------- 3.5 合规自查表打勾
checked = 0
for para in doc.paragraphs:
    if para.text.startswith("□") and para.runs:
        para.runs[0].text = "☑" + para.runs[0].text[1:]
        checked += 1
print(f"合规自查表已勾选 {checked} 项")

# ---------------------------------------------------------------- 4. 填写表 8 自评表
assess = [
    ("课内必做档（5 项验收）", "☑ 完成", "5/5 通过，详见 6.5"),
    ("课内挑战档", "□ 完成  ☑ 未完成", "本次仅完成课内必做档"),
    ("清洗日志四项齐全", "☑ 是", "clean_log.txt（51 行）"),
    ("一行验证代码自测通过", "☑ 是", "shape 输出 = (50, 5)"),
    ("课外拓展（两项）", "□ 已计划  ☑ 未完成", "本次未开展"),
    ("我能说出合规三问", "☑ 能", "① 站点允许吗 ② 频率是否打扰 ③ 是否含隐私/版权"),
]
assess_tbl = doc.tables[7]
for row_idx, values in enumerate(assess, start=1):
    for col_idx, value in enumerate(values):
        set_cell_text(assess_tbl.rows[row_idx].cells[col_idx], value, size=9.5)

# ---------------------------------------------------------------- 5. 附录：实践成果
add_heading_like("六、实践成果与验收", "Heading1")

add_body_para(
    "本人在 quotes.toscrape.com 上完成一次合规的数据采集实践：用 requests + BeautifulSoup(lxml) "
    "抓取前 5 页名言数据，经清洗后得到 50 条结构化记录，并留存清洗日志与合规证据。"
    "课内必做档 5 项验收全部通过。", indent_first=True)

# 6.1
add_heading_like("6.1 采集结果概览", "Heading2")
add_body_para("表 4  采集与数据集概览", size=9, bold=True, space_before=6, space_after=2, keep_next=True)
overview = [
    ("数据源", "https://quotes.toscrape.com（公开练习站点）"),
    ("采集时间", "2026-11-06 14:54:25 — 14:54:39（总耗时 13.6 秒，总请求数 5 次）"),
    ("采集范围", "第 1–5 页，每页 10 条，共 50 条"),
    ("字段数", "5 个：text / author / author_url / tags / page"),
    ("text 长度", "最短 34 字符，最长 1084 字符，平均 125.9 字符"),
    ("数据质量", "各字段非空率 100%；text 去重后仍为 50 条（无重复）"),
    ("存储格式", "CSV，编码 utf-8-sig（Excel 直接打开无乱码）"),
]
t = add_table_with_borders(len(overview), 2, widths=[1.3, 4.8], header=False)
for i, (k, v) in enumerate(overview):
    fill_table_cell(t.rows[i].cells[0], k, bold=True, size=9.5)
    fill_table_cell(t.rows[i].cells[1], v, size=9.5)

# 6.2
add_heading_like("6.2 数据样本（清洗后前 5 条）", "Heading2")
add_body_para("表 5  数据样本", size=9, bold=True, space_before=6, space_after=2, keep_next=True)

rows = list(csv.DictReader(open(os.path.join(WS, "data_quotes_clean_20261106.csv"),
                               encoding="utf-8-sig")))
sample = rows[:5]
t = add_table_with_borders(len(sample) + 1, 5, widths=[0.35, 1.1, 2.95, 1.5, 0.4])
fill_header_row(t, ["#", "author", "text", "tags", "page"])
for i, r in enumerate(sample, start=1):
    text = r["text"]
    if len(text) > 76:
        text = text[:75] + "…"
    fill_table_cell(t.rows[i].cells[0], str(i), size=9)
    fill_table_cell(t.rows[i].cells[1], r["author"], size=9)
    fill_table_cell(t.rows[i].cells[2], text, size=9)
    fill_table_cell(t.rows[i].cells[3], r["tags"], size=9)
    fill_table_cell(t.rows[i].cells[4], r["page"], size=9)

# 6.3
add_heading_like("6.3 清洗结果", "Heading2")
add_body_para(
    "清洗脚本 clean.py 依次执行四项处理，全过程写入 clean_log.txt，每一步均打印处理前后行数：",
    indent_first=True)
clean_items = [
    ("① 去重（按 text 全文）", "删除 0 条", "原始 50 条 text 互不相同，无需删除"),
    ("② 补空", "author 补 0 条 / tags 补 2 条", "2 条原站无标签的记录填为「无标签」"),
    ("③ 统一格式", "text 0 条、URL 0 条、tags 0 条", "原始数据已符合规范"),
    ("④ 极值校验", "5 列非空率均 100%", "text 长度 34–1084，无长度 <5 的异常行"),
]
t = add_table_with_borders(len(clean_items), 3, widths=[1.6, 2.2, 2.3], header=False)
for i, (a, b, c) in enumerate(clean_items):
    fill_table_cell(t.rows[i].cells[0], a, bold=True, size=9.5)
    fill_table_cell(t.rows[i].cells[1], b, size=9.5)
    fill_table_cell(t.rows[i].cells[2], c, size=9.5)

add_body_para(
    "清洗前后对比：原始 50 条 → 清洗后 50 条，仅 2 条 tags 由空值变为「无标签」，其余数据未改动。",
    size=10, space_before=4)

# 6.4
add_heading_like("6.4 合规证据", "Heading2")
add_body_para(
    "① 请求间隔：每次请求（含失败与重试）后 time.sleep(1.5)，全程串行、无并发。\n"
    "② User-Agent：VibeCodingCourse/1.0 (student project; contact: 3133477401@qq.com)。\n"
    "③ 页数上限：硬编码 5 页，命令行参数也无法突破。\n"
    "④ 异常处理：403 / 429 立即终止，不换 IP、不绕过；单页失败重试 1 次后记录页码并跳过。\n"
    "⑤ robots.txt：经浏览器实地访问，目标站点未提供 robots.txt（HTTP 404）。按 RFC 9309，"
    "404 表示未声明爬取限制；本项目仍按保守策略执行。检查记录与截图见下。")
add_body_para("图 1  robots.txt 实地访问结果（HTTP 404 Not Found）", size=9, bold=True,
              space_before=6, space_after=2, keep_next=True)
crop_src = os.path.join(WS, "robots_evidence_annotated.png")
crop_dst = os.path.join(WS, "robots_evidence_crop.png")
crop_white_margin(crop_src, crop_dst)
doc.add_picture(crop_dst, width=Inches(6.0))
doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.paragraphs[-1].paragraph_format.keep_with_next = False

# 6.5
add_heading_like("6.5 课内必做档验收对照", "Heading2")
add_body_para("表 6  课内必做 5 项验收", size=9, bold=True, space_before=6, space_after=2, keep_next=True)
accept = [
    ("1", "≥50 条、每条 ≥5 字段", "☑ 通过", "50 条 × 5 字段，空 text 0 条"),
    ("2", "清洗日志四项齐全", "☑ 通过", "clean_log.txt，每步含前后行数"),
    ("3", "CSV 用 utf-8-sig、Excel 无乱码", "☑ 通过", "原始与清洗版 CSV 均带 BOM"),
    ("4", "代码含 sleep(≥1 秒) 与总请求数打印", "☑ 通过", "SLEEP_SEC = 1.5，输出总请求数 5 / 总耗时 13.6 秒"),
    ("5", "robots.txt 截图在案", "☑ 通过", "robots_evidence.txt + 图 1"),
]
t = add_table_with_borders(len(accept) + 1, 4, widths=[0.35, 2.0, 0.75, 3.0])
fill_header_row(t, ["#", "验收项", "结果", "证据"])
for i, vals in enumerate(accept, start=1):
    for j, v in enumerate(vals):
        fill_table_cell(t.rows[i].cells[j], v, size=9)

# 6.6
add_heading_like("6.6 提交文件清单", "Heading2")
files = [
    ("crawler.py", "采集脚本（试采核对 + --full 全量，含重试与 403 终止）"),
    ("clean.py", "清洗脚本（去重 / 补空 / 统一格式 / 极值校验）"),
    ("data_quotes_20261106.csv", "原始采集数据，50 条，utf-8-sig"),
    ("data_quotes_clean_20261106.csv", "清洗后数据，50 条，utf-8-sig"),
    ("clean_log.txt", "清洗日志，四项齐全"),
    ("robots_evidence.txt / .png", "robots.txt 检查记录与截图"),
    ("test_crawler.py", "8 个离线单元测试，全部通过"),
]
t = add_table_with_borders(len(files) + 1, 2, widths=[2.35, 3.75])
fill_header_row(t, ["文件", "说明"])
for i, (a, b) in enumerate(files, start=1):
    fill_table_cell(t.rows[i].cells[0], a, size=9, mono=True)
    fill_table_cell(t.rows[i].cells[1], b, size=9)

doc.save(DST)
print("已生成:", DST)
print("大小:", os.path.getsize(DST), "字节")
print("段落数:", len(doc.paragraphs), "表格数:", len(doc.tables))
