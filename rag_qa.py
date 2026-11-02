# W7 RAG 学科知识库问答器（加载 → 分块 → 向量化 → 检索＋生成）
#
# 生成环节直接复用 W6 的 llm.LLM（prefer 切换、双向回退全部继承），本文件不另写一套调模型的代码。
#
# 关于依赖：讲义给的骨架用 langchain + Chroma，本机 pip 连不上外网装不了，
# 所以这里内置了一套等价实现，四步一步不少，接口与讲义一致（get_retriever / retrieve /
# build_prompt / rag_qa）：
#   · 分块：500 字、重叠 50 字（与讲义参数一致）
#   · 向量化：直接调 Ollama 的 /api/embed，模型 nomic-embed-text（本地嵌入，数据不出机器）
#   · 向量库：持久化到 chroma_db/vectors.json（已在 .gitignore），换文本要用 rebuild=True
#   · 检索：余弦相似度取 top-k
# 装好 langchain 之后，只要把 get_retriever() 内部换成 Chroma 版即可，其余代码不用动。
#
# 进阶要求（来源标注）：每块都记了来源文件与段号，检索结果带 [来源 第N段]，
# 提示词要求答案末尾注明依据的段号 —— 老师能一眼核对"这句话是哪来的"。
import json
import math
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

CORPUS = weekpath.data_path("等级标准节选.txt")       # 不依赖当前工作目录
PERSIST = weekpath.root_path("chroma_db")             # .gitignore 已排除
STORE_FILE = os.path.join(PERSIST, "vectors.json")

OLLAMA = os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

_store = None


# ── 向量化：调本地嵌入模型，文本不出机器 ──────────────────────────
def _post_json(url, payload, timeout=120):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"})
    # 系统代理会把 127.0.0.1 也送进代理，必须绕开（W5 踩过）
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def embed(text):
    """一句话/一段话 → 向量。走 Ollama /api/embed（旧版可用 /api/embeddings）。"""
    try:
        return _post_json(OLLAMA + "/api/embed", {"model": EMBED_MODEL, "input": text})["embeddings"][0]
    except Exception:
        return _post_json(OLLAMA + "/api/embeddings", {"model": EMBED_MODEL, "prompt": text})["embedding"]


# ── ① 加载 ② 分块 ────────────────────────────────────────────
def split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """先按空行分段，再把小段拼到 size 以内；单段超长才按字数切。

    为什么不是直接每 500 字硬切：标准里的「量化指标总表」是一整块表格，
    硬切会把表头和数据行拆到两块，检索到「四级 1000/3245」却丢了表头那句
    「/前为新增、/后为累计」，模型就读不懂哪个是哪个（实测踩过）。
    按段落切能保证「表头 + 数据行」留在同一块里。
    """
    text = re.sub(r"[ \t]+", " ", text).strip()
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks, buf = [], ""
    for p in paras:
        if len(p) > size:                      # 单段就超长：退回按字数切
            if buf:
                chunks.append(buf)
                buf = ""
            start = 0
            while start < len(p):
                chunks.append(p[start:start + size])
                start += size - overlap
            continue
        if not buf:
            buf = p
        elif len(buf) + 2 + len(p) <= size:
            buf = buf + "\n\n" + p
        else:
            chunks.append(buf)
            buf = p
    if buf:
        chunks.append(buf)
    return chunks


TABLE_HINT = ("（读表说明：每行依次为 等次／级别／音节／汉字／词汇／语法点；"
              "表中的“/”前是本级新增数量，“/”后是截至本级的累计数量。）")


def _enrich(chunk):
    """把「读表说明」绑到含表格行的块上。

    这张表一旦被切成两块，检索到「四级 1000/3245」的块里就没有表头说明，
    模型会看不懂哪个数是新增、哪个是累计（实测两次答案打架）。给块补上表头，
    问题就不再依赖「碰巧检索到了表头那一块」。
    """
    if re.search(r"(初等|中等|高等)\s+(一级|二级|三级|四级|五级|六级|七)", chunk) or "等次" in chunk:
        return TABLE_HINT + "\n" + chunk
    return chunk


def build_store(rebuild=False):
    """建库/加载库：分块 + 向量化 + 落盘。已有库就复用，除非 rebuild。"""
    global _store
    if _store is not None and not rebuild:
        return _store
    if not rebuild and os.path.exists(STORE_FILE):
        with open(STORE_FILE, encoding="utf-8") as f:
            _store = json.load(f)
        return _store

    with open(CORPUS, encoding="utf-8") as f:
        raw = f.read()
    source = os.path.basename(CORPUS)
    items = []
    for i, chunk in enumerate(split_text(raw), 1):
        chunk = _enrich(chunk)          # 含表格的块补上「读表说明」，检索与提示词用同一份文本
        items.append({"id": i, "source": source, "text": chunk, "vec": embed(chunk)})
        print("[build] 块 %d/%d 已向量化" % (i, len(split_text(raw))), end="\r")
    os.makedirs(PERSIST, exist_ok=True)
    with open(STORE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False)
    _store = items
    print("\n[build] 已建库：%d 块 → %s" % (len(items), STORE_FILE))
    return _store


# ── ④ 检索 ──────────────────────────────────────────────────
def _cos(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)


def retrieve_chunks(question, k=3, rebuild=False):
    """问题也向量化，在库里找最相似的 top-k 段。返回带来源的块列表。"""
    qv = embed(question)
    hits = sorted(build_store(rebuild), key=lambda c: -_cos(qv, c["vec"]))[:k]
    return hits


def retrieve(question, k=3, rebuild=False):
    """给提示词用的上下文：每段前面带 [来源 第N段]，方便答案引出处。"""
    return "\n\n".join("[%s 第%d段] %s" % (c["source"], c["id"], c["text"])
                       for c in retrieve_chunks(question, k, rebuild))


def get_retriever(k=3, rebuild=False):
    """保留讲义里的函数名：返回一个可 invoke(question) → 片段列表 的对象。"""
    return _Retriever(k, rebuild)


class _Retriever:
    def __init__(self, k, rebuild):
        self.k, self.rebuild = k, rebuild

    def invoke(self, question):
        return [c["text"] for c in retrieve_chunks(question, self.k, self.rebuild)]


# ── 生成：复用 W6 的统一入口 ─────────────────────────────────
def build_prompt(question, ctx):
    return ("根据以下资料回答问题，资料中没有的内容就如实说“资料中未提及”。\n"
            "注意：资料里的“X 级”就是 HSK X 级，说法不同但等价的要据此作答，不要因为措辞不完全一样就说未提及。\n"
            "每个片段前的 [文件名 第N段] 是出处；回答末尾请注明你依据的段号。\n\n"
            "%s\n\n问题：%s" % (ctx, question))


def rag_qa(question, prefer="local", k=3, rebuild=False):
    """检索 → 拼提示词 → 交给 llm.ask()。返回 (答案, 命中的块)。"""
    from llm import LLM          # week06 的模块，靠 weekpath 才能 import 到

    hits = retrieve_chunks(question, k, rebuild)
    ctx = "\n\n".join("[%s 第%d段] %s" % (c["source"], c["id"], c["text"]) for c in hits)
    return LLM().ask(build_prompt(question, ctx), prefer=prefer), hits


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    prefer = "local"
    if args and args[0] in ("local", "api"):
        prefer = args.pop(0)
    q = " ".join(args) or "HSK 四级要求掌握多少词汇和语法点？"
    answer, hits = rag_qa(q, prefer=prefer, rebuild="--rebuild" in sys.argv)
    print("【命中片段】")
    for h in hits:
        print("  [%s 第%d段] %s…" % (h["source"], h["id"], h["text"][:60].replace("\n", " ")))
    print("\n【回答】\n" + answer)
