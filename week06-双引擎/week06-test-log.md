# W6 双引擎 · 边界测试记录

> 环境：Windows 11 25H2 · Python 3.14.3 · Ollama 0.40.6 · 本地 `qwen2.5:0.5b`（Q4_K_M，397 MB）· 云端 `deepseek-chat`
> 代码：`week06_双引擎/llm.py`（`LocalEngine` / `APIEngine` / `LLM.ask(prompt, prefer=...)`）
> 测试时间：2026-10-26 13:40–13:50
> 统一题目：**「给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项」**（四组用同一题，方便比质量）


## 一、边界测试记录（4 组）

| # | ① 测试条件 | ② 实际走了哪个引擎 | ③ 耗时与答案质量一句话点评 | ④ 是否符合预期 / 不符合怎么改 |
|---|---|---|---|---|
| 1 | **Ollama 开**，`prefer='local'` | 本地 `qwen2.5:0.5b`（无切换） | 首次冷启 **112.90 s**（模型未常驻，其中装载 42.7 s）；模型常驻后**热调用 0.78 s**。质量：**答非所问**——没出题，直接列 A/B/C/D"答案"，还编出"这句诗表达了愚公移山的雄伟气势" | 符合"本地优先"。但冷启 100 s+ 说明这台机器（电源方案＝静音）第一次调用很慢 → 上课演示前先用 `ollama run` 热一次 |
| 2 | **Ollama 关**（杀掉 11434 的进程），`prefer='local'` | 本地**连接被拒**（WinError 10061）→ 自动切 **云端** `deepseek-chat` | 3.35 s。质量：原文 + 题干 + 四个选项 + 干扰项（"山不会变高"）都合理，**可直接用** | 符合预期，这是最关键的一组：回退日志完整（失败原因 + 切换方向都打出来了） |
| 3 | **Ollama 开**，`prefer='api'` | 云端 `deepseek-chat`（无切换） | 2.70 s。质量同第 2 组，措辞略不同，可直接进教案 | 符合预期（正常走云端，不碰本地） |
| 4 | **Ollama 开**，`prefer='api'`，但把 `DEEPSEEK_API_KEY` 改成无效值（模拟密钥失效/欠费） | 云端 **401 AuthenticationError** → 自动切 **本地** `qwen2.5:0.5b` | 104.53 s（模型未常驻，含装载）。质量：**又跑偏**——编出"自次第而移，自高而下"的伪古文，10 个问题全是"从题干中你读出了什么" | 双向回退成立（云端挂 → 本地接住）。但调用方原来只能翻控制台日志才知道"是谁答的" → **已改**：给 `LLM` 加 `last_engine`，调用后可直接读 |

> 四组里第 2 组和第 4 组是"计划外"的失败路径，日志价值最高：**回退要留下原因，不能只写"成功了"**。


## 二、原始日志（逐组证据）

### 组 1：Ollama 开 + prefer='local'
`ext
[LLM] prefer=local -> 先试 本地(qwen2.5:0.5b)
[LLM] 成功：本地(qwen2.5:0.5b) 返回，用时 112.90 s
好的，我将为你出一道 HSK4 阅读理解题：
题目：愚公移山的故事流传了几千年。现在，让我们继续来解这个谜题……（没出四选项题）

```text
[LLM] 成功：本地(qwen2.5:0.5b) 返回，用时 0.78 s
好的，以下是《愚公移山》这道 HSK4 阅读理解题的答案：
1. 选择 A：这句诗表达了愚公移山的雄伟气势和决心。
[LLM] 本次实际引擎：本地(qwen2.5:0.5b)
```

单独用 `/api/chat` 测得冷装载 `load_duration = 42.73 s`、生成 52.6 tok/s；模型常驻后 158–179 tok/s（W5 同一台机器、同一模型是 313 tok/s）。

### 组 2：Ollama 关 + prefer='local'（自动切云端）★

```text
[LLM] prefer=local -> 先试 本地(qwen2.5:0.5b)
[LLM] 失败：本地(qwen2.5:0.5b)（RuntimeError: 本地 Ollama 不可用（http://127.0.0.1:11434/api/chat）：<urlopen error [WinError 10061] 由于目标计算机积极拒绝，无法连接。>）
[LLM] 切换：本地(qwen2.5:0.5b) 不可用，改用 云端(deepseek-chat) 兜底重试
[LLM] 成功：云端(deepseek-chat) 兜底返回，用时 3.35 s
```

### 组 3：Ollama 开 + prefer='api'

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)
[LLM] 成功：云端(deepseek-chat) 返回，用时 2.70 s
```

### 组 4：prefer='api' 但密钥失效（自动切本地）★

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)
[LLM] 失败：云端(deepseek-chat)（AuthenticationError: Error code: 401 - {'error': {'message': 'Authentication Fails, Your api key: ****test is invalid ...
[LLM] 切换：云端(deepseek-chat) 不可用，改用 本地(qwen2.5:0.5b) 兜底重试
[LLM] 成功：本地(qwen2.5:0.5b) 兜底返回，用时 104.53 s
```

复现方式：`python -c "import os; os.environ['DEEPSEEK_API_KEY']='sk-invalid'; import llm; print(llm.LLM().ask('...', prefer='api'))"`（`weekpath.load_env()` 不覆盖已存在的变量，所以假密钥优先生效）。


## 三、结论

1. **双向兜底都成立。** 本地挂 → 云端（组 2，3.35 s 接住）；云端挂 → 本地（组 4，104 s 接住）。`prefer` 只决定"先试谁"，不决定"只能用它"。
2. **兜底不是免费的。** 组 4 回退到本地用了 104 s，比云端正常回答的 3 s 慢 30 倍——用户感知上就是"卡住了"。真实产品里要配超时/进度提示，不能默默等。
3. **双引擎解决"可用性"，不解决"质量"。** 同一道题：云端给出的是完整 HSK4 阅读题（原文+四个选项+答案），本地 0.5b 给的是"这句诗表达了……"和伪古文。所以第 8 周做助手时，**本地当草稿/离线兜底，云端当定稿**这条分工不能反。
4. **环境和电源方案会吃掉一半速度。** 这台机器当前是"静音"电源方案（GPU 空闲 180 MHz），本地从 W5 的 313 tok/s 掉到 52–180 tok/s，冷装载从 4 s 涨到 42.7 s。测速前先切"平衡/高性能"，并插电。
5. **这次测试改出来的一处代码**：`LLM.last_engine`。没有它，程序回退后调用方不知道答案来自哪个引擎；加上之后，日志与后续计费/隐私判断都能对齐。


## 四、复现命令

```powershell
cd D:\week06_双引擎

# 组 1 / 组 3
python llm.py local "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"
python llm.py api   "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"

# 组 2：先关掉 Ollama（托盘退出，或杀掉 11434 的进程）再跑 local
python llm.py local "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"

# 组 4：见上文 python -c 命令
```
