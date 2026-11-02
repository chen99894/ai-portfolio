# W6 双引擎封装 —— 此后所有周统一经此调用：from llm import LLM
# 依赖：pip install openai requests python-dotenv
#   requests 只用于本地 http 直连；机房装不上时自动退回标准库 urllib，接口不变。
#
# ── 作业 1 选型说明（评分点）─────────────────────────────────────────────
# 三选一里我选 **多轮对话（messages 列表记忆）**，理由：
#   1. 后面 W8 华文小助手、W11 智能体都要"接着上一句说"，多轮是必经之路；
#      重试和费用估算是"锦上添花"，多轮是"没有就做不下去"。
#   2. 本地 /api/chat 本来就吃 messages 列表，改造成本集中在"历史怎么存、失败怎么回滚"，
#      不会动 ask() 这个对外接口（W7 起全部 from llm import LLM，签名不能变）。
# 为什么不选另外两项：
#   · 失败重试：本地冷装载实测 40 s+、整次调用 100 s+（见 week06_test_log.md 第 1 组），
#     再重试 2 次等于让用户干等 5 分钟，比直接回退更糟；而且回退已经兜住了可用性。
#   · 耗时/费用估算：本地不按 token 计费，估出来的"费用"是假的；云端单价还会变，
#     维护一张价目表反而容易过期。真要算账，用 week05 的实测数据比代码里硬编码更靠谱。
# ────────────────────────────────────────────────────────────────
import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402  跨周导入 + 加载 .env

weekpath.load_env()

import openai  # noqa: E402

try:
    import requests  # noqa: E402
except ImportError:  # 没装 requests 也能跑
    requests = None

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
DEEPSEEK_BASE = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
CLOUD_MODEL = os.getenv("CLOUD_MODEL", "deepseek-chat")

# 首次调用要把模型装载进显存（实测 0.5b 4–43 s，4b 更久）。
# 给 5 s 会误判成"服务挂了"，所以本地也给 120 s。
LOCAL_TIMEOUT = 120


def _post_json(url, payload, timeout):
    """本地 http 直连：有 requests 用它，没有就退回 urllib，两种走法结果一致。"""
    if requests is not None:
        # 机房/校园网常配系统代理，必须显式关掉；否则 localhost 也会被送去代理 → 连接被拒
        r = requests.post(url, json=payload, timeout=timeout, proxies={"http": None, "https": None})
        r.raise_for_status()
        return r.json()
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class LocalEngine:
    """本地引擎（Ollama）：数据不出机器、断网可用、不按次计费。

    能力上限由模型大小决定：0.5b 只够干"格式固定 + 人工可校验"的活。
    """

    def __init__(self, model=None):
        self.model = model or os.getenv("LOCAL_MODEL", "qwen2.5:0.5b")
        self.name = "本地(%s)" % self.model

    def chat(self, messages, temperature=0.7, max_tokens=800):
        """messages 直接透传给 Ollama：多轮对话就是把它整个历史发过去。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        try:
            data = _post_json(OLLAMA_URL, payload, LOCAL_TIMEOUT)
        except Exception as e:
            raise RuntimeError("本地 Ollama 不可用（%s）：%s" % (OLLAMA_URL, e))
        self.last_finish = data.get("done_reason")  # "stop" 正常 / "length" 被 num_predict 截断
        return data["message"]["content"]

    def ask(self, prompt, **kw):
        return self.chat([{"role": "user", "content": prompt}], **kw)


class APIEngine:
    """云端引擎（DeepSeek / OpenAI 兼容接口）：复杂任务、本地失败兜底。

    注意：openai.OpenAI(...) 在 api_key 为 None 时会直接抛错。
    若在构造 LLM 时就建客户端，那么没配密钥的同学连"纯本地"模式都跑不起来。
    所以改成**按需创建**：第一次真正调用云端时才建客户端。
    """

    def __init__(self, base_url=None, model=None):
        self.base_url = base_url or DEEPSEEK_BASE
        self.model = model or CLOUD_MODEL
        self.name = "云端(%s)" % self.model
        self._client = None

    def _get_client(self):
        if self._client is None:
            key = os.getenv("DEEPSEEK_API_KEY")
            if not key:
                raise RuntimeError(
                    "未配置 DEEPSEEK_API_KEY：复制 .env.example 为 .env 并填入密钥；"
                    "纯本地模式请用 ask(..., prefer='local')"
                )
            self._client = openai.OpenAI(base_url=self.base_url, api_key=key)
        return self._client

    def chat(self, messages, temperature=0.7, max_tokens=800):
        r = self._get_client().chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self.last_finish = r.choices[0].finish_reason  # "stop" 正常 / "length" 被截断
        return r.choices[0].message.content

    def ask(self, prompt, **kw):
        return self.chat([{"role": "user", "content": prompt}], **kw)


class LLM:
    """统一入口：LLM().ask(prompt, prefer='local'|'api')。

    两边互为兜底，任一侧挂了都不会让程序直接崩：
      prefer='local' 本地不可用（Ollama 没开/模型没拉）→ 自动切云端；
      prefer='api'   云端不可用（断网/超时/没配密钥/密钥失效）→ 自动切本地。

    多轮用法（作业 1）：
      llm = LLM(); llm.chat("愚公移山讲了什么？"); llm.chat("用 HSK4 水平再讲一遍")
      —— 第二句会自动带上第一轮的问答；llm.reset() 清空历史，llm.messages 可读可查。
    ask() 依旧是无状态单轮，W7 起的 from llm import LLM 不受影响。
    """

    def __init__(self, local_model=None, system=None):
        self.local = LocalEngine(local_model)
        self.api = APIEngine()
        # 最近一次真正回答的引擎名与结束原因：调用方据此记录"谁答的""是不是被截断"
        self.last_engine = None
        self.last_finish = None
        # 多轮对话历史：整段发给引擎，成功后才把助手回复追加进去
        self.messages = [{"role": "system", "content": system}] if system else []

    # ── 对外：单轮 ──────────────────────────────────────────────
    def ask(self, prompt, prefer="local", **kw):
        return self._run([{"role": "user", "content": prompt}], prefer, **kw)

    # ── 对外：多轮（作业 1）─────────────────────────────────────
    def chat(self, text, prefer="local", **kw):
        """把这一句接在历史后面发出去；成功才落历史，失败自动回滚这一句。"""
        self.messages.append({"role": "user", "content": text})
        try:
            ans = self._run(self.messages, prefer, **kw)
        except Exception:
            self.messages.pop()  # 失败的这一轮不留进历史，否则下一轮会带着脏上下文
            raise
        self.messages.append({"role": "assistant", "content": ans})
        return ans

    def reset(self):
        """清空历史（保留 system）。"""
        if self.messages and self.messages[0]["role"] == "system":
            del self.messages[1:]
        else:
            self.messages = []

    # ── 内部：回退逻辑 ──────────────────────────────────────────
    def _run(self, messages, prefer, **kw):
        if prefer == "local":
            first, second = self.local, self.api
        elif prefer == "api":
            first, second = self.api, self.local
        else:
            raise ValueError("prefer 只能是 'local' 或 'api'，收到：%r" % (prefer,))

        print("[LLM] prefer=%s -> 先试 %s（历史 %d 条）" % (prefer, first.name, len(messages)))
        t0 = time.perf_counter()
        try:
            ans = first.chat(messages, **kw)
            self.last_engine = first.name
            self.last_finish = getattr(first, "last_finish", None)
            print("[LLM] 成功：%s 返回，用时 %.2f s，finish=%s"
                  % (first.name, time.perf_counter() - t0, self.last_finish))
            return ans
        except Exception as e:
            first_err = "%s: %s" % (type(e).__name__, str(e).strip().splitlines()[0] if str(e) else "")
            print("[LLM] 失败：%s（%s）" % (first.name, first_err[:160]))
            print("[LLM] 切换：%s 不可用，改用 %s 兜底重试" % (first.name, second.name))

        t1 = time.perf_counter()
        try:
            ans = second.chat(messages, **kw)
        except Exception as e2:
            second_err = "%s: %s" % (type(e2).__name__, str(e2).strip().splitlines()[0] if str(e2) else "")
            raise RuntimeError("两个引擎都不可用 —— %s（%s）；%s（%s）"
                               % (first.name, first_err, second.name, second_err))
        self.last_engine = second.name
        self.last_finish = getattr(second, "last_finish", None)
        print("[LLM] 成功：%s 兜底返回，用时 %.2f s，finish=%s"
              % (second.name, time.perf_counter() - t1, self.last_finish))
        return ans


if __name__ == "__main__":
    prefer = sys.argv[1] if len(sys.argv) > 1 else "local"
    question = " ".join(sys.argv[2:]) or "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"
    llm = LLM()
    print(llm.ask(question, prefer=prefer))
    print("[LLM] 本次实际引擎：%s，finish=%s" % (llm.last_engine, llm.last_finish))
