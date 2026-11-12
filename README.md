# dhm123

AI 应用开发实训（Vibe Coding）课程作业仓库。

## 课程成果索引

| 课次 | 主题 | 入口文件 |
|---|---|---|
| 第 5 / 6 课 | RAG 问答项目（离线建库 + 检索 + 对话） | `index.py`、`ask.py`、`app.py` |
| 第 8 课 | 名言数据采集与清洗（50 条） | `crawler.py`、`clean.py` |
| 第 9 课 | 单文件交互式数据分析报告（3 问 3 图） | `analysis_report.py` → `report.html` |

---

## 第 8 课 · 数据采集与清洗

从 `quotes.toscrape.com` 合规采集名言数据 → 清洗 → 验收。课内必做 5 项**全部通过**。

### 文件清单

| 文件 | 说明 |
|---|---|
| `crawler.py` | 采集脚本（requests + BeautifulSoup/lxml） |
| `clean.py` | 清洗脚本（去重 / 补空 / 统一格式 / 极值校验） |
| `test_crawler.py` | 离线单元测试（8 个用例，全通过） |
| `data_quotes_20261106.csv` | 原始采集结果（50 条，utf-8-sig） |
| `data_quotes_clean_20261106.csv` | 清洗后结果（50 条，utf-8-sig） |
| `clean_log.txt` | 清洗日志（四项齐全，每步含前后行数） |
| `robots_evidence.txt` / `.png` | robots.txt 检查记录与截图（实测 HTTP 404） |
| `VERIFY.md` | 课内必做 5 项验收报告（脚本生成） |
| `verify_acceptance.py` | 验收自检脚本，可重复运行 |

### 数据字段

`text` / `author` / `author_url` / `tags`（多个用 `|` 连接）/ `page`

- 条数 50，覆盖第 1–5 页，每页 10 条
- `text` 长度 min 34 / max 1084 / 平均 125.9
- 5 列非空率 100%（tags 的 2 条空值在清洗阶段补为「无标签」）

### 合规设计

- 每次请求（含失败与重试）后 `time.sleep(1.5)`，全程串行无并发
- `User-Agent: VibeCodingCourse/1.0 (student project; contact: 3133477401@qq.com)`
- 总页数硬上限 5 页；403 / 429 立即终止，不绕过
- robots.txt 实测 **HTTP 404**（站点未提供），按 RFC 9309 属未声明限制

### 验收（5/5）

| # | 验收项 | 结果 | 证据 |
|---|---|---|---|
| 1 | ≥50 条、每条 ≥5 字段 | ✅ | 50 条 × 5 字段，空 text 0 |
| 2 | 清洗日志四项齐全 | ✅ | `clean_log.txt` |
| 3 | CSV 用 utf-8-sig、Excel 无乱码 | ✅ | 两个 CSV 均带 BOM |
| 4 | 代码含 sleep(≥1秒) 与总请求数打印 | ✅ | `SLEEP_SEC = 1.5`，输出「总请求数 5 / 总耗时 13.6 秒」 |
| 5 | robots.txt 截图在案 | ✅ | `robots_evidence.txt` + `robots_evidence_annotated.png` |

---

## 第 9 课 · 数据分析与可视化

把第 8 课的数据集做成一份单文件交互式报告 `report.html`（Plotly，JS 内联，断网可开）。

### 三个业务问题

| # | 问题 | 字段 | 统计量 | 图表 |
|---|---|---|---|---|
| 1 | 哪位作者被收录最多？前 5 名各多少条？ | `author` | 计数 | 横向条形图 |
| 2 | 出现频率最高的 10 个标签是什么？ | `tags`（拆分后） | 计数 | 横向条形图 |
| 3 | 名言文本长度分布如何？有无异常短句？ | `text`（长度） | 分布 / 中位数 | 直方图 |

### 关键结论

- **Albert Einstein 被收录最多（8 条）**
- Top5 作者合计 26 条，占全部 50 条的 52.0%
- **inspirational 是最常用标签（9 次）**
- 文本长度中位数 83.5 字符，区间 34–1084

### 数字核对（两种方法）

| 数字 | pandas 结果 | 第二验证方法 | 一致 |
|---|---|---|---|
| Einstein 条数 | 8 | `collections.Counter` 逐行计数 = 8 | ✅ |
| Top5 合计 | 26 | `most_common(5)` 求和 = 26 | ✅ |
| 标签总数 | 123 | 逐行 `split("\|")` 累加 = 123 | ✅ |
| 长度中位数 | 83.5 | `statistics.median` = 83.5 | ✅ |

### 图表精修（6 条要求全部落实）

条形降序 / 去竖直网格留横向 / 条末标数值 / 单主色+灰只强调第一名 / 标题改结论句式 / 坐标轴加名称单位。

---

## 运行

```bat
:: 第 8 课：采集与清洗
python crawler.py            :: 试采前 5 条核对
python crawler.py --full     :: 全量采集 50 条
python clean.py              :: 清洗并生成 clean_log.txt

:: 第 9 课：生成分析报告
python analysis_report.py    :: 输出 report.html（双击即可打开）
```

依赖：`pip install requests beautifulsoup4 lxml pandas plotly`

---

## 提交文档

- `第8次课-实践成果-提交版.docx` —— 采集与清洗工作纸 + 成果附录
- `第9次课-实践成果-提交版.docx` —— 分析工作纸 + 成果附录 + 提交清单
