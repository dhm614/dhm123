# -*- coding: utf-8 -*-
"""把 404 截图加上「访问地址 + 时间」标注，生成完整证据图（中文用微软雅黑渲染）。"""
from PIL import Image, ImageDraw, ImageFont

SRC = r"D:\deepseekworkspace\robots_evidence.png"
DST = r"D:\deepseekworkspace\robots_evidence_annotated.png"
FONT_CN = r"C:\Windows\Fonts\msyh.ttc"

shot = Image.open(SRC).convert("RGB")
w, h = shot.size
top = 100

canvas = Image.new("RGB", (w, h + top), "#ffffff")
d = ImageDraw.Draw(canvas)
f_title = ImageFont.truetype(FONT_CN, 24)
f_bar = ImageFont.truetype(FONT_CN, 16)

d.rectangle([0, 0, w, 56], fill="#1f3b57")
d.text((24, 14), "robots.txt 检查证据（浏览器实际访问截图）", font=f_title, fill="#ffffff")

d.rectangle([0, 56, w, top], fill="#eef1f5")
d.rounded_rectangle([20, 66, w - 20, 92], radius=8, fill="#ffffff", outline="#c8cfd8")
bar = ("https://quotes.toscrape.com/robots.txt     |     访问时间 2026-11-06 15:24 (Asia/Shanghai)"
       "     |     HTTP 404 Not Found")
d.text((36, 71), bar, font=f_bar, fill="#333333")

canvas.paste(shot, (0, top))
canvas.save(DST)
print("已生成:", DST, canvas.size)
