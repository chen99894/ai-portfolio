# W8 阶段项目一：学科智能问答助手 v1.0
#
# 组装不写新轮子：
#   W2 提示词库  → SYSTEM_HINT（定人设：你是谁、面向谁、要什么）
#   W6 双引擎    → llm.LLM().ask(prefer=...)（本地优先、云端兜底、双向回退）
#   W7 知识库    → rag_qa.retrieve() + build_prompt()（先查资料，再答，带出处）
# 本文件只做「粘合层」：一个 use_rag 开关 + 一个 prefer 透传 + 一层异常兜底。
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  让跨周 import 生效（llm 在 week06、rag_qa 在 week07）

weekpath.load_env()

from llm import LLM  # noqa: E402  W6 双引擎
from rag_qa import retrieve, build_prompt  # noqa: E402  W7 知识库

# ── W2 提示词库的落地：一句话定人设 ──────────────────────────
SYSTEM_HINT = (
    "你是国际中文教学助手，面向 HSK3–4 学习者与授课教师。"
    "回答用中文，先给结论再给要点；涉及数字、等级、规则时必须以资料为依据，没有依据就说明。"
)

# 演示用三问：语法点 / 数字指标 / 活动设计，覆盖「知识问答」与「生成创造」两类
# 选的都是知识库里真有答案的题——演示要证明「带资料能答对」，不是证明「会答未提及」。
DEMO_QUESTIONS = [
    "HSK4 要求掌握多少个语法点？累计多少个？",
    "HSK4 词汇量要求是多少？",
    "《愚公移山》可以设计什么课堂活动？",
]

LAST = {}   # 最近一次调用的元信息（谁答的、多久、有没有检索）


def answer(question, use_rag=True, prefer="local", k=3):
    """统一回答入口：use_rag 决定要不要先查资料，prefer 决定先找本地还是云端。"""
    llm = LLM()
    t0 = time.perf_counter()

    if use_rag:
        hits = retrieve_chunks_safe(question, k)
        ctx = "\n\n".join("[%s 第%d段] %s" % (h["source"], h["id"], h["text"]) for h in hits)
        prompt = SYSTEM_HINT + "\n\n" + build_prompt(question, ctx)
    else:
        hits = []
        prompt = SYSTEM_HINT + "\n\n" + question

    text = llm.ask(prompt, prefer=prefer)

    LAST.update({
        "question": question, "use_rag": use_rag, "prefer": prefer,
        "engine": llm.last_engine, "sec": round(time.perf_counter() - t0, 2),
        "hits": [(h["source"], h["id"]) for h in hits],
    })
    return text


def retrieve_chunks_safe(question, k=3):
    """检索单独兜一层：向量库/嵌入模型没准备好时，降级成「不检索也照答」。

    这样一场演示里某个组件挂了，不会把整个助手带停——「能演示」的最低要求。
    """
    try:
        from rag_qa import retrieve_chunks
        return retrieve_chunks(question, k=k)
    except Exception as e:
        print("[warn] 检索失败，降级为纯对话：%s" % e)
        return []


def run_demo(prefer="local"):
    """三问三答：每个问题都打一问一答，任何一问失败都不影响其余两问。"""
    for i, q in enumerate(DEMO_QUESTIONS, 1):
        print("=" * 60)
        print("Q%d：%s" % (i, q))
        try:
            text = answer(q, use_rag=True, prefer=prefer)
            print("A%d（%s，%.2fs，资料 %d 段）：\n%s"
                  % (i, LAST["engine"], LAST["sec"], len(LAST["hits"]), text.strip()))
        except Exception as e:
            # 常见：Ollama 没启动 / 没 pull nomic-embed-text / 没配云端密钥
            print("A%d：[运行失败] %s: %s" % (i, type(e).__name__, e))


def main():
    args = sys.argv[1:]
    if not args:
        run_demo()
        return

    # 课堂演示建议：python assistant_v1.py --prefer api
    # （本地 0.5b 读表格会把相邻两列读串，见 README「已知问题」）
    if "--ask" not in args and "--prefer" in args:
        run_demo(prefer=args[args.index("--prefer") + 1])
        return

    # 单问模式：python assistant_v1.py --ask "问题" [--no-rag] [--prefer api]
    q = "把字句的教学难点有哪些？"
    use_rag, prefer = True, "local"
    if "--ask" in args:
        q = args[args.index("--ask") + 1]
    if "--no-rag" in args:
        use_rag = False
    if "--prefer" in args:
        prefer = args[args.index("--prefer") + 1]
    try:
        print(answer(q, use_rag=use_rag, prefer=prefer))
        print("\n[meta] %s" % LAST)
    except Exception as e:
        print("[运行失败] %s: %s" % (type(e).__name__, e))
        sys.exit(1)


if __name__ == "__main__":
    main()

# 发布（在仓库根目录执行）：
#   git add . && git commit -m "W8: 助手 v1.0"
#   git tag -a v1.0 -m "学科智能问答助手 v1.0" && git push origin main --tags
# 然后到网页端 Release/发行版 选 v1.0 标签，填功能/安装/用法。
