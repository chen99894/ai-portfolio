# 官方 RAG 流水线 ↔ 我的 rag_qa.py / assistant_v1.py（5 行映射）

> 对照对象：LangChain 官方 2-Step RAG 教程、Datawhale llm-universe C3/C4（只读，不搬代码）。
> 结论先说：官方那套用的是「组件拼装」，我这套是「同样五步、手写最小实现」——**步骤对得上，组件可以逐个替换**，这正是本周要看清的事。

| # | 官方流水线（LangChain / llm-universe） | 我的实现（week07·week08） | 差异与可迁移点 |
|---|---|---|---|
| 1 | **Load + Split**：`TextLoader` + `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)` | `rag_qa.split_text()`：先按空行分段再拼到 500 字，含表格的块自动绑上「读表说明」 | 官方按字符硬切；我这份资料是表格，硬切会把表头和数据行切开，所以改成按段落切——**切块策略要跟着数据走，不是跟着默认参数走** |
| 2 | **Embed + Store**：`OllamaEmbeddings(nomic-embed-text)` + `Chroma(persist_directory=...)` | 直接 POST `/api/embed` 取 768 维向量，落盘到 `chroma_db/vectors.json`，检索时算余弦 | 官方封装了向量库（HNSW、元数据过滤、持久化）；我这里 8 块语料用暴力余弦足够，**语料上千块就该换回 Chroma** |
| 3 | **Retrieve**：`retriever.invoke(question)` 取 top-k | `retrieve_chunks(question, k=3)`，返回带 `[来源 第N段]` 和相似度的块 | 官方返回 Document 对象；我返回 dict——**接口形式不同，语义一致**：问题向量化 → 相似度排序 → top-k |
| 4 | **Prompt + Generate**：PromptTemplate 拼上下文，`llm.invoke()` 生成 | `build_prompt()` 拼「系统人设 + 资料 + 问题 + 引用要求」，交 `llm.ask(prefer=...)` | 我的 `llm.ask` 自带本地/云端双向回退，官方示例只有单一路径——**这是课程积木叠加出来的增量** |
| 5 | **Deploy + Evaluate**：Streamlit 部署 + C5 系统评估 | 命令行 `assistant_v1.py`；评估用 W7 幻觉对照表（同一问题裸答 vs RAG） | 官方有 RAGAS 之类的自动指标；我用人工对照表，样本小但**每条都能回原文核对**，W15 再上界面 |

## 一句话

官方教程教我的是「**组件可以换**」：loader 换学科资料、embeddings 换成本地 nomic、vector store 换成本地 Chroma，应用逻辑一行不用改。
我这次恰好把「组件」都手写了一遍，所以更清楚每个盒子里装的是什么——**改得动才算真懂**。
