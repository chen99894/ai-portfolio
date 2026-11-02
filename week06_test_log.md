# W6 双引擎 · 边界测试记录（6 组）

> 环境：Windows 11 25H2 · Python 3.14.3 · Ollama 0.40.6 · 本地 `qwen2.5:0.5b`（Q4_K_M，397 MB）· 云端 `deepseek-chat`
> 代码：`week06_双引擎/llm.py`（`LocalEngine` / `APIEngine` / `LLM.ask|chat`，双向回退 + 多轮历史 + `last_engine / last_finish`）
> 测试时间：2026-10-26 13:40 与 2026-11-02 13:00 两轮（同机同网）
> 统一题目：**「给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项」**（六组同一题，方便比质量）

---

## 一、边界测试记录（6 组）

| # | ① 测试条件（Ollama 开/关、prefer 取值） | ② 实际走了哪个引擎（看切换日志） | ③ 耗时与答案质量一句话点评 | ④ 是否符合预期 / 不符合怎么改 |
|---|---|---|---|---|
| 1 | **Ollama 开**，`prefer='local'` | 本地 `qwen2.5:0.5b`（无切换），`finish=stop` | **117.39 s**（模型未常驻，含装载；静音电源下很慢）。质量：**答非所问**——出成"选成语填空"，还把故事讲错（"他很聪明，但因为山太高，他无法搬动它……终于，终于"） | 符合"本地优先"。但冷启近 2 分钟，上课演示前必须先 `ollama run` 热一次，否则学生以为死机 |
| 2 | **Ollama 关**（杀掉 11434 进程），`prefer='local'` | 本地**连接被拒**（WinError 10061）→ 自动切 **云端** `deepseek-chat` | **2.94 s**。质量：原文 + 题干 + 四选项齐备，干扰项合理，**可直接用** | 符合预期。★最关键的一组：失败原因 + 切换方向都打出来了 |
| 3 | **Ollama 开**，`prefer='api'` | 云端 `deepseek-chat`，`finish=stop` | **2.43 s**。质量同第 2 组，可直接进教案 | 符合预期（正常走云端，不碰本地） |
| 4 | **Ollama 开**，`prefer='api'`，`DEEPSEEK_API_KEY` 改成无效值 | 云端 **401 AuthenticationError** → 自动切 **本地** | 切本地后 **2.78 s**（模型已常驻），`finish=stop`。质量：又是"以下是《愚公移山》的HSK4阅读理解题"就没了，**没给出题** | 双向回退成立。但回退后调用方原来只能翻日志 → 已加 `last_engine` 字段 |
| 5 | **Ollama 开**，`prefer='api'`，`DEEPSEEK_BASE_URL` 指向不存在的端口（模拟**云端不可用**） | 云端 **APIConnectionError** → 自动切 **本地** | 切本地 **1.82 s**。质量：开头"标题：愚公移山"后跑偏，仍是本地水准 | 符合预期（与第 4 组对称：一个是"密钥错"，一个是"连不上"） |
| 6 | `prefer='api'`，**`max_tokens=25`** 调小 | 云端 `deepseek-chat`，`finish=length` | **1.74 s**，答案断在半句（"愚公为什么决定要移走两座大山？"后直接截断，没有选项和答案） | 符合预期：`finish=length` 能提前发现截断，调用方应据此提示"换大模型/提高上限"，而不是把半句当成品 |

> 第 2、5 组是"本地挂/云端挂"的对称证据；第 6 组证明"参数调小会截断，而且能从 `finish` 认出来"。

---

## 二、回退日志原文（逐组抄录）

### 组 1：Ollama 开 + prefer='local'

```text
[LLM] prefer=local -> 先试 本地(qwen2.5:0.5b)（历史 1 条）
[LLM] 成功：本地(qwen2.5:0.5b) 返回，用时 117.39 s，finish=stop
当然可以。以下是《愚公移山》的 HSK4 阅读理解题：
【题目】：根据下面的成语故事，选择正确的成语来填空：
在山的脚下，有一个人叫做愚公，他很聪明，但因为山太高，他无法搬动它。他每天都要用铲子……
```

### 组 2：Ollama 关 + prefer='local'（自动切云端）★

```text
[LLM] prefer=local -> 先试 本地(qwen2.5:0.5b)（历史 1 条）
[LLM] 失败：本地(qwen2.5:0.5b)（RuntimeError: 本地 Ollama 不可用（http://127.0.0.1:11434/api/chat）：<urlopen error [WinError 10061] 由于目标计算机积极拒绝，无法连接。>）
[LLM] 切换：本地(qwen2.5:0.5b) 不可用，改用 云端(deepseek-chat) 兜底重试
[LLM] 成功：云端(deepseek-chat) 兜底返回，用时 2.94 s，finish=stop
**题目：**
《愚公移山》的故事中，愚公为什么决定要移山？
A……
```

### 组 3：Ollama 开 + prefer='api'

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 1 条）
[LLM] 成功：云端(deepseek-chat) 返回，用时 2.43 s，finish=stop
**题目：**
《愚公移山》的故事中，愚公为什么决定要移山？
```

### 组 4：prefer='api' + 密钥无效（云端挂 → 切本地）★

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 1 条）
[LLM] 失败：云端(deepseek-chat)（AuthenticationError: Error code: 401 - {'error': {'message': 'Authentication Fails, Your api key: ****test is invalid (request_id: 3e915be9-dfc0-4b06-b036-6de81）
[LLM] 切换：云端(deepseek-chat) 不可用，改用 本地(qwen2.5:0.5b) 兜底重试
[LLM] 成功：本地(qwen2.5:0.5b) 兜底返回，用时 2.78 s，finish=stop
好的，以下是《愚公移山》的HSK4阅读理解题：
```

### 组 5：prefer='api' + 云端地址不可达（对称回退）

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 1 条）
[LLM] 失败：云端(deepseek-chat)（APIConnectionError: Connection error.）
[LLM] 切换：云端(deepseek-chat) 不可用，改用 本地(qwen2.5:0.5b) 兜底重试
[LLM] 成功：本地(qwen2.5:0.5b) 兜底返回，用时 1.82 s，finish=stop
好的，以下是一道 HSK4 阅读理解题：
标题：愚公移山
```

### 组 6：prefer='api' + max_tokens=25（观察截断）

```text
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 1 条）
[LLM] 成功：云端(deepseek-chat) 返回，用时 1.74 s，finish=length
**题目：**
《愚公移山》的故事中，愚公为什么决定要移走两座大山？
```

---

## 三、作业 1 验证：多轮对话（messages 记忆）

```text
--- 第 1 轮 ---
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 1 条）
[LLM] 成功：云端(deepseek-chat) 返回，用时 3.58 s，finish=stop
《愚公移山》讲了愚公不畏艰难、坚持不懈地带领子孙挖山不止，最终感动天帝派神将山移走的故事。
--- 第 2 轮（只问「改写上一句」，看它记不记得）---
[LLM] prefer=api -> 先试 云端(deepseek-chat)（历史 3 条）
[LLM] 成功：云端(deepseek-chat) 返回，用时 1.08 s，finish=stop
愚公决定挖掉两座大山。他带着家人每天挖山，不怕困难。最后，天帝被感动了，派人把山搬走了。
历史条数： 4
```

第二轮没有重复原句，却准确改写了第一轮的答案 → 历史确实带上了（`历史 3 条` = 用户1 + 助手1 + 用户2）。
失败时 `chat()` 会把自己刚追加的那条弹掉，保证下一轮不带脏上下文；`reset()` 清空历史。

---

## 四、反思：什么任务固定走本地，什么固定走云端（约 250 字）

判断依据三条，按优先级：

**① 数据能不能离开这台机器。** 学生作文、成绩、评语、未公开教案，一律本地，这条**不看质量**——质量再好也不能传。
**② 错了要不要命。** 语法讲解、教案成稿这类要直接进课堂的，本地 0.5b 编过"这句诗表达了……""提高他们的英语水平""自次第而移"，必须云端。
**③ 量大不大、是否需要批量。** 格式固定的批量活（例句、格式转换、初稿）本地又快又免费，产出后人工抽检即可。
所以：固定本地的＝含学生个人信息的材料、断网课堂演示、大批量格式化草稿；固定云端的＝语法讲解、教案成稿、事实型长文。多数时候是混合：本地脱敏起稿 → 云端润色；本地批量 → 云端抽检。一句话：**先看隐私红线，再看错误代价，最后看调用量。**

---

## 五、对照验收标准自查

| 档 | 标准 | 本记录 |
|---|---|---|
| 达标 | 三个类都在，两个引擎都能调，异常有提示，本地失败能切云端且不崩溃 | ✅ 组 2 |
| 良好 | `prefer` 可切换、回退双向；边界记录 ≥5 组且带回退日志原文 | ✅ 6 组，组 2–6 均抄了原文 |
| 优秀 | 能说明"隐私任务走本地、复杂任务走云端"的判断依据 | ✅ 第四节按三条优先级写清 |

---

## 六、复现命令

```powershell
cd D:\week06_双引擎

# 组 1 / 组 3
python llm.py local "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"
python llm.py api   "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"

# 组 2：先关掉 Ollama（托盘退出，或杀掉 11434 的进程）再跑 local
python llm.py local "给《愚公移山》出一道 HSK4 阅读理解题，只要题目和四个选项"

# 组 4：假密钥（weekpath.load_env 不覆盖已存在的变量，所以假密钥优先生效）
python -c "import os; os.environ['DEEPSEEK_API_KEY']='sk-invalid'; import llm; print(llm.LLM().ask('...', prefer='api'))"

# 组 5：把云端地址指到空端口
python -c "import os; os.environ['DEEPSEEK_BASE_URL']='http://127.0.0.1:9/v1'; import llm; print(llm.LLM().ask('...', prefer='api'))"

# 组 6：调小 max_tokens 看截断
python -c "import llm; l=llm.LLM(); l.ask('...', prefer='api', max_tokens=25); print(l.last_finish)"   # length
```
