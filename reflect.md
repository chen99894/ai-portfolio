# W8 开源对照 · 反思（300 字）

**① 我的 rag_qa.py 与官方 2-Step RAG 差在哪一步？**
六步（Load→Split→Embed→Store→Retrieve→Prompt+Generate）我都做了，差的不在步骤，在**组件**：官方用 `TextLoader`、`RecursiveCharacterTextSplitter`、`OllamaEmbeddings`、`Chroma`，我这台机器 pip 连不上外网装不了 langchain，于是用 `open()`+`split_text()`、`/api/embed`+`vectors.json`+余弦手写了一遍。所以严格说不是"没做"，是"做法不同、叫法不同"——但也因此我知道每个盒子里装的是什么。

**② 要从 2-Step 走到 Agentic RAG，先补什么能力？**
先把 `retrieve()` 变成模型**能主动调用的工具**（W9 的 function calling），而不是写死在 `answer()` 的第一步；再补两个判断：什么时候不该检索（闲聊）、检索回来不相关怎么办。还要把工具调用历史放进多轮上下文，否则模型记不住自己查过什么。

**③ llm-universe 没有 LICENSE，为什么只能参考思路不能复制代码？**
没写 LICENSE ≠ 公共领域，按默认规则是"保留所有权利"；可以读、可以学、可以署名引用，但把代码搬进仓库就等于侵占别人的著作权。这和 `.env` 不入仓是同一件事：**边界先于方便**——两条都是别人一眼就能验证的诚信约束，破了就是整份作业作废，不是"改一下就好"。
