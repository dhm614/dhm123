# RAG 问答项目（离线建库 + 命令行问答）

对 `docs/` 下的文档做检索问答：`index.py` 离线切块并生成向量索引，`ask.py` 加载索引后用余弦相似度检索 Top3，把命中原文交给对话模型作答，回答末尾强制标注来源。

## 环境

- Windows + Python 3.12
- 依赖：`requests`、`numpy`、`python-dotenv`

## 配置（.env，不入库）

```
DEEPSEEK_API_KEY=...
API_BASE_URL=https://api.deepseek.com/v1

EMBEDDING_KEY=...
EMBEDDING_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v4

CHAT_KEY=            # 留空则回退 DEEPSEEK_API_KEY
CHAT_BASE_URL=       # 留空则回退 API_BASE_URL
CHAT_MODEL=deepseek-flash
```

## 使用

```
python index.py     # 建库，生成 index.json
python ask.py       # 提问，输入 q 退出
```

## 文件

| 文件 | 说明 |
| --- | --- |
| `docs/celeste-chapters.md` | 数据源：《蔚蓝》全章节攻略，5102 字 |
| `index.py` | 离线建库：固定长度切分 + 批量向量化 |
| `ask.py` | 命令行问答：余弦检索 Top3 + 对话模型作答 |
| `index.json` | 默认索引（400/60，15 块 × 1024 维） |
| `index_200_30.json` | 切分对比实验：200/30（30 块） |
| `index_800_120.json` | 切分对比实验：800/120（8 块） |

## 切分参数对比（同一份 10 题、同一模型、K=3）

| 参数(块/重叠) | 总块数 | 命中题数 | 出处正确数 |
| --- | --- | --- | --- |
| 200 / 30 | 30 | 9/10 | 9/10 |
| 400 / 60 | 15 | 10/10 | 10/10 |
| 800 / 120 | 8 | 10/10 | 10/10 |

200/30 下第 1 题失败：200 字的前言块抢占 Top1，含答案的块未进 Top3。
