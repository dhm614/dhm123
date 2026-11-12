# 课内必做 5 项验收报告

生成时间：2026-11-06  |  通过：**5/5**

| # | 验收项 | 结果 | 证据 |
|---|---|---|---|
| 1 | ① ≥50 条 + 每条 ≥5 字段 | ✅ 通过 | 条数=50，字段=['text', 'author', 'author_url', 'tags', 'page']，空值统计={'text': 0, 'author': 0, 'author_url': 0, 'tags': 2, 'page': 0} |
| 2 | ② 清洗日志四项齐全 (+每步行数) | ✅ 通过 | 去重=有；补空=有；统一格式=有；极值校验=有；行数前后对比=有 |
| 3 | ③ CSV utf-8-sig（Excel 无乱码） | ✅ 通过 | data_quotes_20261106.csv: BOM=有；data_quotes_clean_20261106.csv: BOM=有 |
| 4 | ④ sleep(≥1 秒) + 打印总请求数 | ✅ 通过 | SLEEP_SEC=1.5，打印总请求数=有，打印总耗时=有 |
| 5 | ⑤ robots.txt 检查在案 | ✅ 通过 | 记录文件=有，截图=有，实测状态=HTTP 404（站点无 robots.txt，按 RFC 9309 未声明限制） |

## 数据文件

- 原始：`data_quotes_20261106.csv`（50 条）
- 清洗后：`data_quotes_clean_20261106.csv`（50 条）

## 数据样本（清洗后前 5 条）

| # | author | text | tags | page |
|---|---|---|---|---|
| 1 | Albert Einstein | “The world as we have created it is a process of our thinkin… | change|deep-thoughts|thinking|world | 1 |
| 2 | J.K. Rowling | “It is our choices, Harry, that show what we truly are, far … | abilities|choices | 1 |
| 3 | Albert Einstein | “There are only two ways to live your life. One is as though… | inspirational|life|live|miracle|miracles | 1 |
| 4 | Jane Austen | “The person, be it gentleman or lady, who has not pleasure i… | aliteracy|books|classic|humor | 1 |
| 5 | Marilyn Monroe | “Imperfection is beauty, madness is genius and it's better t… | be-yourself|inspirational | 1 |
