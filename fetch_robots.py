# -*- coding: utf-8 -*-
"""检查 robots.txt 并保存证据（含 URL、抓取时间、UA、状态码、原文/结论）。

注意：quotes.toscrape.com 实测返回 404 —— 站点没有 robots.txt。
按 RFC 9309，404 表示「未声明爬取限制」，属于可访问；本脚本把这一事实原样记录。
"""
import requests
from datetime import datetime

URL = "https://quotes.toscrape.com/robots.txt"
HOME = "https://quotes.toscrape.com/"
UA = "VibeCodingCourse/1.0 (student project; contact: 3133477401@qq.com)"
HEADERS = {"User-Agent": UA}

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
r = requests.get(URL, headers=HEADERS, timeout=30)
status = r.status_code
text = r.text

if status == 200:
    conclusion = "robots.txt 存在，需逐条检查 Disallow 路径"
    body = text
elif status == 404:
    conclusion = ("站点未提供 robots.txt（HTTP 404）。按 RFC 9309，404 = 未声明爬取限制；"
                  "本项目仍按「保守合规」处理：只采公开列表页、每次请求间隔 1.5 秒、UA 标明课程身份。")
    body = "（无 robots.txt 内容，服务器返回 404 Not Found）"
else:
    conclusion = f"robots.txt 返回 HTTP {status}，按保守合规处理并人工确认"
    body = text

# 顺带确认首页可正常访问（证明确实是同一站点、公开页面）
home = requests.get(HOME, headers=HEADERS, timeout=30)
home_ok = home.status_code == 200 and 'class="quote"' in home.text

evidence = f"""robots.txt 检查记录（对应课程「合规自查表」第 2 项）
============================================================
目标站点   : https://quotes.toscrape.com
robots 地址: {URL}
检查时间   : {now} (Asia/Shanghai)
请求 UA    : {UA}
robots 状态: HTTP {status}
首页状态   : HTTP {home.status_code}，页面含名言列表: {'是' if home_ok else '否'}
Content-Type (robots): {r.headers.get('Content-Type')}

结论
------------------------------------------------------------
{conclusion}

robots.txt 原文
------------------------------------------------------------
{body}
============================================================
配套截图: robots_evidence.png（浏览器 headless 实际访问该 URL 的画面）
"""
with open("robots_evidence.txt", "w", encoding="utf-8") as f:
    f.write(evidence)
print(evidence)
