# W8 五步流水线映射表（rag_mapping.md）

> 第三列**照着我自己仓库里的代码填**（`week07_RAG/rag_qa.py`、`week08_助手v1.0/assistant_v1.py`），不是抄讲义。
> 一个前提：本机 `pip` 连不上外网，`langchain` / `chromadb` 装不了，所以我的六步是**手写的最小实现**——步骤一一对应，组件不同名。

| # | 官方流水线 / llm-universe 章节 | 我自己的代码（真实函数名/类名） |
|---|---|---|
| 1 | **Load + Split**<br>官方：loaders / splitters 可替换<br>llm-universe：C3「数据处理：读取、清洗与切片」 | `rag_qa.split_text(text, size=500, overlap=50)`：先按空行分段再拼到 500 字（不硬切），`_enrich()` 给含表格的块补「读表说明」。语料 = `data/等级标准节选.txt` + `data/愚公移山.txt`。**没用** `TextLoader` / `RecursiveCharacterTextSplitter` |
| 2 | **Embed + Store**<br>官方：embeddings / vector store 可替换<br>llm-universe：C3「词向量及向量知识库」「搭建并使用向量数据库」 | `rag_qa.embed()` 直接 POST Ollama `/api/embed`，模型 `nomic-embed-text`（768 维，本地、数据不出机器）；`rag_qa.build_store()` 把块与向量写进 `chroma_db/vectors.json` 持久化。**没用** `OllamaEmbeddings` / `Chroma` |
| 3 | **Retrieve**<br>官方：retriever 取 top-k<br>llm-universe：C4「基于 LangChain 搭建检索问答链」 | `rag_qa.retrieve_chunks(question, k=3)`：问题向量化后与每块算余弦（`_cos`），排序取前 k；`rag_qa.retrieve()` 再拼成 `[文件名 第N段]` 的上下文。`assistant_v1.answer()` 里 `use_rag=True` 时**先 retrieve 再 ask**，False 时直接 ask |
| 4 | **Prompt + Generate**<br>官方：PromptTemplate + LLM<br>llm-universe：C4「将 LLM 接入 LangChain」 | `rag_qa.build_prompt(question, ctx)` 拼四段：`SYSTEM_HINT`（W2 人设）+ 读表说明 + 检索片段 + 问题，并要求"资料里没有就说未提及、末尾注明段号"；最后调 **W6 的** `LLM().ask(prefer="local"\|"api")`，双向回退 |
| 5 | **Deploy + Evaluate**<br>官方：部署 + 评估<br>llm-universe：C4「Streamlit 部署」+ C5「系统评估与优化」 | 评估：`week07_RAG/hallucination_log.md`（6 组裸答 vs 带资料）+ `week08_助手v1.0/answer_log.md`（8 组，含引擎与耗时）。部署：现在只有 CLI，W15 用 Streamlit 做成页面（计划：问题框 + 答案区 + 出处折叠 + "本次用了哪个引擎"角标） |
