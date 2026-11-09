# 学科智能问答助手 v1.0

## 功能
- 基于 RAG 的学科问答：先检索本地知识库（HSK 等级标准 + 课文），再让模型照着资料回答，并给段号出处。
- 支持「纯对话 / 基于资料」两种模式（`use_rag` 开关），以及本地 / 云端两种引擎（`prefer` 参数）。
- 单问失败不影响其余问题：检索失败会降级为纯对话，引擎失败会自动切另一边。

## 怎么装
- `pip install -r requirements.txt`（只需 openai + python-dotenv；本地直连用标准库，不需要 requests）
- `ollama pull qwen2.5:0.5b && ollama pull nomic-embed-text`（本地模型 + 本地嵌入，数据不出机器）
- 复制 `.env.example` 为 `.env`，填入 `DEEPSEEK_API_KEY`；`.env` 已在 `.gitignore` 里，绝不入库

## 怎么用
- `cd week08_助手v1.0 && python assistant_v1.py`（三问三答，默认本地引擎）
- `python assistant_v1.py --prefer api`（三问三答走云端，**课堂演示建议用这条**，0.5b 读表不稳）
- `python assistant_v1.py --ask "HSK4 词汇量要求是多少？" --prefer api`（单问）；加 `--no-rag` 关检索做对比

## 已知问题
- 本地 `qwen2.5:0.5b` 读表格能力弱：给它「76/286」这类数据，它会把相邻两列读串（实测把语法点答成 210、把音节 1800 当成语法点），**涉及数字请用 `prefer="api"`**。
- 知识库目前只有两份资料（等级标准节选、愚公移山），问知识库外的问题（如"把字句教学难点"）会如实回「资料中未提及」——这是设计行为，补资料后 `rag_qa.py --rebuild` 即可。
- 换过 `data/` 里的文本必须重建向量库，否则检索到的还是旧库。
- 未启动 Ollama 时本地模式会报错；可设 `prefer="api"` 走云端。
