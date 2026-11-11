# W8 互评表 · 被评对象：程荟霖（f25210104）

> 评阅人：陈丽琪（f25210102）
> 被评仓库：https://github.com/chl9052/ai-portfolio （`main` 分支）
> 核对时间：2026-11-11 16:4x
> 核对方式：**GitHub API 静态核对**（`W8/` 目录文件树、`W8/README.md`、`W8/assistant_v1.py`、tag、Release 页）。没有对方的 Ollama 环境与密钥，所以"实跑"一项核对的是代码路径、异常兜底与仓库里留存的运行凭据，**不写"我跑通了"**。
> 纪律：只描述现象，不打分、不评价人。

## ① 能不能跑

现象：
- `W8/assistant_v1.py`（1.3 KB）在，结构是 `answer(question, use_rag=True, prefer="local")` + 三个问题的 `for` 循环 + 每题 `try/except` 打印 `A: [运行失败] …`，与讲义骨架一致；依赖的 `llm.py`、`rag_qa.py` 都在同目录，import 不会跨目录丢。
- 仓库里有 `W8/终端运行截图凭据.png`（287 KB）和根目录 `w7_rag_run.png`，能看出确实跑过。
- 与讲义骨架的差异：**没有命令行参数**。`--prefer`、`--no-rag` 都只能用改代码或改函数默认值的方式切；互评时想对同一问题做"带资料 / 纯对话"对比，只能改代码重跑。
- `assistant_v1.py` 用 `load_dotenv()`（不传路径），读的是**当前工作目录**下的 `.env`；`weekpath` 那套跨周 import 没走，是 `sys.path.insert` + 同目录文件。

## ② README 能复现吗

现象（`W8/README.md`，四段式在，但有两处照做会卡住）：
1. 「怎么用」写 **"在 `week08_助手v1.0` 目录下运行"**，而仓库里这个目录叫 **`W8/`** —— 照抄这行 `cd` 会失败。
2. 「怎么装」写"复制 `.env.example` 为 `.env`"，但仓库里**没有 `.env.example` 这个文件**（根目录和 `W8/` 都没有）—— 第二步无法照做。
3. `pip install -r requirements.txt` 没写路径，而 `requirements.txt` 在 `W8/` 下；从仓库根执行会报找不到文件。

三处都在"怎么装 / 怎么用"这两段，属于最容易让互评者卡住的位置。

## ③ Release 发了吗

现象：
- 有 tag `v1.0`（指向 `c9b6d28`）。
- Release 页面已发布（标题「学科智能问答助手 v1.0」，2026-11-09 13:53），**是正式发布，不是 draft**。
- 正文只有三行：功能（RAG 问答、纯对话/基于资料两种模式）、安装（`pip install -r requirements.txt`）、使用（`python assistant_v1.py`）。**没有**"已知问题"、没有交付文件清单、安装命令同样没写路径。

## ④ 有没有已知限制

现象：
- `W8/README.md` 的「已知问题」写了 1 条：未启动 Ollama 时本地模式会报错，可设 `prefer="api"` 走云端。方向是对的，但没提"没配密钥时云端也会失败"、也没提 0.5B 读数字不可靠。
- Release 正文里没有"已知问题"这一节。
- 红线方面：仓库里**没有 `.env`、没有密钥文件**（文件树里只有 `README`、`.py`、`.md`、`.txt`、两张 png），这一项是干净的。

## 三条可操作建议（只描述现象，供参考）

1. README 里把 `week08_助手v1.0` 改成实际目录 `W8/`，并给 `requirements.txt` 补上 `W8/` 前缀——两行字解决两个"照着装会失败"。
2. 仓库里补一个 `W8/.env.example`（只有 `DEEPSEEK_API_KEY=` 一行即可），或者在 README 里改成"在 `W8/` 下新建 `.env`，写 `DEEPSEEK_API_KEY=...`"。
3. `assistant_v1.py` 加 `argparse` 的 `--prefer` 与 `--no-rag` 两个开关，成本很低；这样互评和老师演示都不用改代码就能对比两种模式。

## 结论（只描述现象）

四维中：**tag + Release** 已具备（正文偏薄）；**已知限制**有一条且在理；**README 复现**存在目录名与 `.env.example` 两处硬伤；**能不能跑**有运行截图与完整异常兜底，但缺少可切换的命令行参数。
