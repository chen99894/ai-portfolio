# W9 手写最小工具调用循环（不用框架）
# 四个工具：get_time / calc（白名单 AST）/ hsk_level / text_difficulty（第 4 个，作业 2）
# 依赖：pip install openai python-dotenv jieba
import ast
import csv
import datetime
import json
import operator
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  数据路径 + 加载 .env

weekpath.load_env()

import jieba  # noqa: E402
import openai  # noqa: E402

VOCAB = weekpath.data_path("生词表.csv")

_client = None
_vocab = None


def get_client():
    global _client
    if _client is None:
        key = os.getenv("DEEPSEEK_API_KEY")
        if not key:
            raise RuntimeError("未配置 DEEPSEEK_API_KEY，请先在 .env 中填写")
        _client = openai.OpenAI(
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
            api_key=key)
    return _client


def _load_vocab():
    """词 → 等级 的字典，只读一次。"""
    global _vocab
    if _vocab is None:
        with open(VOCAB, encoding="utf-8") as f:
            _vocab = {row["词汇"].strip(): int(row["HSK等级"])
                      for row in csv.DictReader(f) if row.get("词汇")}
    return _vocab


# ── 工具 1：查当前时间 ──────────────────────────────────────
def get_time():
    return str(datetime.datetime.now())


# ── 工具 2：安全计算（白名单 AST，绝不使用裸 eval）────────────
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval_node(node):
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("只允许数字与 + - * / ** % 运算")


def calc(expr):
    """教学演示用：只做四则运算。为什么不用 eval？
    因为 eval 会执行任意 Python 代码（`__subclasses__()` 能绕过 __builtins__ 限制，
    读到文件与环境变量），是典型的安全反模式。"""
    try:
        return str(_eval_node(ast.parse(str(expr), mode="eval")))
    except ZeroDivisionError:
        return "错误：除数为 0"
    except Exception as e:
        return "拒绝计算：%s" % e


# ── 工具 3：查生词 HSK 等级 ─────────────────────────────────
def hsk_level(word):
    table = _load_vocab()
    w = str(word).strip()
    if w in table:
        return "%s 是 %s 级" % (w, table[w])
    return "未找到 %s" % w


# ── 工具 4（作业 2）：课文难度评估 ───────────────────────────
def text_difficulty(text, level="4"):
    """输入一段课文与目标等级，输出生词覆盖率与超纲词列表。

    口径：用 jieba 切词 → 只保留含汉字的词 → 逐词查生词表。
      在表内且 ≤ 目标等级 → 达标词
      在表内但 > 目标等级 → 超纲词
      不在表内          → 表外词（人名、地名、古语等，单列，不算超纲）
    覆盖率 = 达标词 / 总词数。
    """
    words = [w for w in jieba.cut(str(text)) if re.search(r"[\u4e00-\u9fa5]", w)]
    table = _load_vocab()
    lvl = int(level)
    hit, over, unseen = [], [], []
    for w in words:
        g = table.get(w)
        if g is None:
            unseen.append(w)
        elif g <= lvl:
            hit.append(w)
        else:
            over.append(w)

    def uniq(xs):
        out = []
        for x in xs:
            if x not in out:
                out.append(x)
        return out

    total = len(words) or 1
    return json.dumps({
        "目标等级": lvl,
        "总词数": len(words),
        "覆盖率": round(len(hit) / total, 3),
        "达标词数": len(hit),
        "超纲词": uniq(over),
        "表外词": uniq(unseen),
    }, ensure_ascii=False)


TOOLS = {"get_time": get_time, "calc": calc,
         "hsk_level": hsk_level, "text_difficulty": text_difficulty}

SYS = ("你是国际中文助教。可用工具只有这 4 个：\n"
       "1. get_time：查当前时间，无参数，如 get_time()\n"
       "2. calc：四则运算，参数是算式字符串，如 calc('35*24')\n"
       "3. hsk_level：查词语的 HSK 等级，如 hsk_level('把')\n"
       "4. text_difficulty：评估课文难度，两个参数（课文, 目标等级），"
       "如 text_difficulty('愚公移山的故事', '4')\n"
       '如需调用，只输出一行 JSON，格式：{"tool": "工具名", "args": [参数]}；\n'
       "可以一次输出多个调用（每行一个 JSON）；一次只处理一件事也可以。\n"
       "绝不编造不存在的工具名；无需工具时直接回答。")


def parse_calls(txt):
    """容错解析：剥 ```json 围栏、抓 JSON 块、支持一行一个的并列调用。"""
    s = (txt or "").strip().replace("```json", "").replace("```", "").strip()
    try:
        obj = json.loads(s)
        return [obj] if isinstance(obj, dict) else []
    except Exception:
        pass
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            obj = json.loads(m.group())
            if isinstance(obj, dict):
                return [obj]
        except Exception:
            pass
    calls = []
    for blk in re.findall(r"\{[^{}]*\}", s):
        try:
            obj = json.loads(blk)
        except Exception:
            continue
        if isinstance(obj, dict):
            calls.append(obj)
    return calls


TRACE = []   # 轨迹：每一轮的原始输出 / 解析结果 / 工具返回


def run(user_msg, max_calls=2):
    msgs = [{"role": "system", "content": SYS}, {"role": "user", "content": user_msg}]
    for rnd in range(1, max_calls + 1):
        txt = get_client().chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=msgs).choices[0].message.content

        calls = [c for c in parse_calls(txt)
                 if isinstance(c.get("tool"), str) and c.get("tool") in TOOLS]
        TRACE.append({"轮次": rnd, "模型原始输出": txt,
                      "解析到的调用": calls, "工具返回": []})
        if not calls:
            return txt                       # 没点名工具 → 当普通回答

        results = []
        for call in calls:
            args = call.get("args") or []
            if not isinstance(args, list):
                msg = "工具参数格式错误：%r" % (args,)
            else:
                try:
                    msg = "%s(%r) → %s" % (call["tool"], args, TOOLS[call["tool"]](*args))
                except Exception as e:
                    msg = "工具执行失败：%s" % e
            results.append(msg)
            TRACE[-1]["工具返回"].append(msg)

        msgs += [{"role": "assistant", "content": txt},
                 {"role": "user", "content": "工具返回：%s。请据此作答。" % "；".join(results)}]

    # 到上限强制收口，避免无限循环烧 token
    final = get_client().chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=msgs).choices[0].message.content
    TRACE.append({"轮次": "收口", "模型原始输出": final, "解析到的调用": [], "工具返回": []})
    return final


def main():
    args = sys.argv[1:]
    q = " ".join(a for a in args if a != "--trace") or ("请依次查询两件事：1. '把'字的 HSK 等级是多少？"
                                                        "2. 现在的时间是多少？")
    if not args:
        q = "请依次查询两件事：1. '把'字的 HSK 等级是多少？2. 现在的时间是多少？"
    print("用户输入：", q)
    answer = run(q)
    print("助手：", answer)
    if "--trace" in args or not args:
        print("\n———— 调用轨迹 ————")
        for step in TRACE:
            print("[轮次 %s] 模型输出：%s" % (step["轮次"], step["模型原始输出"].strip()))
            for r in step["工具返回"]:
                print("         工具返回：%s" % r)
        print("——————————————————")


if __name__ == "__main__":
    main()
