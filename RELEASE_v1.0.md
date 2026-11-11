# 学科智能问答助手 v1.0

《人工智能在学习环境中的应用与实践》第 8 周阶段项目一。把 W2 提示词库、W6 双引擎 `llm.py`、W7 知识库 `rag_qa.py` 三块积木用一层粘合层串成完整助手——**组装，不是重写**。

## 功能

- **基于 RAG 的学科问答**：`answer(question, use_rag=True, prefer="local")`。开 RAG 先检索《国际中文教育中文水平等级标准》节选与《愚公移山》教学资料，再让模型照着资料回答，答案带 `[文件名 第N段]` 出处，可回原文核对。
- **一个开关两种模式**：`use_rag=True` 基于资料 / `False` 纯对话，同一套代码；`prefer="local" | "api"` 决定先找本地还是云端。
- **双引擎双向回退**：本地 Ollama 挂了自动切云端，云端不可用（断网/没密钥/密钥失效）自动切本地，切换原因与耗时打印在日志里。
- **演示不中断**：三问三答覆盖语法点、数字指标、课堂活动；任一问失败打印「[运行失败] 原因」后继续，不会三问三崩。
- **出处可单独调出**：`--sources` 把命中的片段、段号与相似度单独列出来，答案与依据分开核对；`--k` 可调检索条数。
- **记录可复核**：`answer_log.md` 留了 3 问 × 开/关 RAG × 本地/云端共 8 组原始输出。

## 怎么装

需要 Python 3.10+，并已安装 Ollama。

```bash
git clone https://github.com/chen99894/ai-portfolio.git
cd ai-portfolio
python -m pip install -r week08_助手v1.0/requirements.txt
ollama pull qwen2.5:0.5b
ollama pull nomic-embed-text
cp .env.example .env        # 填入 DEEPSEEK_API_KEY；纯本地演示可不配
```

`.env` 已在 `.gitignore` 里，**不会入库**。

## 怎么用

```bash
# 三问三答（默认本地引擎）
python week08_助手v1.0/assistant_v1.py

# 课堂演示建议走云端：本地 0.5B 读表格会串行（见「已知问题」）
python week08_助手v1.0/assistant_v1.py --prefer api

# 单问 + 关掉检索做对比
python week08_助手v1.0/assistant_v1.py --ask "HSK4 词汇量要求是多少？" --prefer api
python week08_助手v1.0/assistant_v1.py --ask "HSK4 词汇量要求是多少？" --prefer api --no-rag

# 把出处单独调出来（段号 + 相似度 + 片段预览），可配合 --k 3 调检索条数
python week08_助手v1.0/assistant_v1.py --ask "HSK4 词汇量要求是多少？" --prefer api --sources --k 3
```

## 实测对比（同一批问题，开/关 RAG）

| 问题 | 关 RAG | 开 RAG |
|---|---|---|
| HSK4 语法点 | 「100 个，累计 400」❌ | 「新增 76，累计 286」✅ 依据第2段 |
| HSK4 词汇量 | 「1200 词」❌ | 「新增 1000，累计 3245」✅ |
| 愚公移山课堂活动 | 通用四大类，无出处 | 「分角色朗读 / 辩论 / 成语接龙」✅ 依据第4段 |

## 已知问题

- **本地 0.5B 读表不稳**：实测把「76/286」读成「210/1800」，把四级词汇答成 11092。演示与验收请用 `--prefer api`。
- **知识库只有两份资料**（等级标准节选、愚公移山），问「把字句教学难点」这类库外问题，合格表现是回「资料中未提及」——这是设计行为，补语料后 `--rebuild` 即可。
- **换过 `data/` 里的文本必须重建向量库**，否则检索到的还是旧库。
- **没有 `.env` 时云端不可用**：本次发布环境未配置密钥，所以云端路径只有「回退到本地」的证据，没有云端真实作答的截图。
- 未启动 Ollama 时本地检索与生成本地都会失败。

## 本次交付内容

| 文件 | 说明 |
|---|---|
| `week08_助手v1.0/assistant_v1.py` | 粘合层：`answer()` + `use_rag` 开关 + `prefer` 透传 + 异常兜底 |
| `week08_助手v1.0/answer_log.md` | 演示记录 8 组（四要素：问题/模式/引擎/输出与点评） |
| `week08_助手v1.0/README.md` | 四段式 README（功能/怎么装/怎么用/已知问题） |
| `week08_助手v1.0/requirements.txt` | 依赖清单 |
| `week08_助手v1.0/rag_mapping.md` | 官方 5 步流水线 ↔ llm-universe 章节 ↔ 我的真实函数名 |
| `week08_助手v1.0/reflect.md` | 官方教程对照的 300 字反思（答三问） |
| `week08_助手v1.0/read_notes.md` | 官方 Retrieval 文档与 llm-universe C3/C4 的三句阅读笔记 |
| `week08_助手v1.0/改造运行记录.txt` | B 路径改造点（`--sources` / `--k`）的终端运行证据 |
| `week08_助手v1.0/peer_review.md` | 指定对象互评表（只描述现象） |
| `week08_助手v1.0/w8_说明_已知问题为什么要诚实写.md` | 200 字说明 |
| `week08_助手v1.0/w9_预习_工具清单.md` | W9 预习：两个待接入工具（输入/输出） |
| `week07_RAG/rag_qa.py`、`week06_双引擎/llm.py` | 上游积木，本版本未改动 |

## 复现证据

- W6 边界测试 6 组（本地挂→云端、云端挂→本地、`max_tokens` 截断）：`week06_双引擎/week06_test_log.md`
- W7 幻觉对照 6 组（裸答 vs 带资料）：`week07_RAG/hallucination_log.md`
- W8 演示记录：`week08_助手v1.0/answer_log.md`

## 致谢与许可

- 参考 LangChain 官方 2-Step RAG 教程与 Datawhale llm-universe 的章节对照，**只读思路、未复制其代码入库**；llm-universe 仓库未附 LICENSE，按默认规则保留所有权利，此处仅署名引用。
- 语料为课程整理节选，来源与核对说明见 `data/README.md`。
- 本项目为课程作业，使用 AI 辅助编写；方案选择与结果验证由本人完成。
