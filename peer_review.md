# W8 互评表 · 被评对象：刘静（JIZHI-AI-666）

> 评阅人：陈丽琪（f25210102）
> 被评仓库：https://github.com/JIZHI-AI-666/ai-course-lab
> 核对时间：2026-11-09 13:4x
> 核对方式：**GitHub API 静态核对**（仓库文件树、`week08_助手v1.0/` 文件、README、tag、Release 说明页）。我**没有**对方的模型环境与密钥，所以"实跑"一项只核对代码路径与兜底，**不写"我跑通了"**。
> 纪律：只描述看到的现象，不打分、不评价人。

## ① 能不能跑

现象：
- `week08_助手v1.0/assistant_v1.py`（5.7 KB）存在，入口 `main()` + `answer()` 分工清楚。
- 命令行通过 argparse 提供 `--no-rag`、`--prefer {local,api}`、`--json`，以及自由提问（`nargs="*"`）；不填问题则跑内置 `QUESTIONS` 三问（把字句 / HSK4 词汇量 / 愚公移山活动）。
- 每题包在 `try/except` 里，失败打印 `A: [运行失败] 原因` 后继续下一题，三问不会因为一问崩掉整场。
- 检索环节的 import 与调用（`retrieve`、`build_prompt`、`retrieve_documents`）都来自 `week07_RAG/rag_qa.py`，没有在 `week08` 里另写一套调模型/检索代码——**粘合层没有重复实现**。

未能核实的：本地是否 100% 跑通三问（缺对方 Ollama 环境与语料库）。

## ② README 能复现吗

现象：
- 仓库根 README 是四段式：**功能 / 怎么装 / 怎么用 / 已知问题**，另附「本次交付内容」「致谢与许可声明」。
- 「怎么装」是可复制的四步：`git clone` → `python -m venv .venv` → `pip install -r week08_助手v1.0/requirements.txt` → `ollama pull qwen2.5:0.5b` 与 `nomic-embed-text`；还写了"代理拉不动嵌入模型时用 F16 文件导入 + `EMBED_MODEL` 环境变量"的替代路径。
- 「怎么用」给了能直接粘的命令，并标了在哪个目录执行（仓库根）。
- `requirements.txt` 列了 9 个依赖（langchain 四件套、chromadb、openai、requests、python-dotenv、rich），与 `rag_qa.py`/`llm.py` 的 import 对得上。

一处小现象：`assistant_v1.py` 用 `sys.path.insert(0, dirname(dirname(__file__)))` 算仓库根，所以**从任何目录运行都能 import 到 `weekpath`**；README 写的"在仓库根目录运行"其实是多余限制，但不影响复现。

## ③ Release 发了吗

现象：
- 远端有 tag `v1.0`（指向 `f6ad005`）。
- Release 页面已发布，标题「学科智能问答助手 v1.0」，正文含：功能 5 条（RAG/双引擎/来源可追溯/演示不中断/记录可复核）、怎么装、怎么用、已知问题、交付文件清单、致谢与许可（点明参考 LangChain 官方教程与 Datawhale llm-universe 但**未复制其代码**，并说明 llm-universe 无 LICENSE、仅署名引用）。

tag 与 Release 两件都齐，不只有 tag。

## ④ 有没有已知限制

现象：README「已知问题」写了 5 条，且都是"可验证的具体的"，不是套话：
1. 未启动 Ollama 时本地检索与生成都失败，`prefer="api"` 只解决生成、替代不了本地嵌入；
2. 知识库**不含**「把字句教学难点」与「愚公移山课堂活动」，开 RAG 的合格表现就是「资料中未提及」；
3. 0.5B 模型数值不可靠（实测把"累计 3245"答成 1000，纯对话答 2600）；
4. 本次发布环境没配云端密钥，所以**没有云端真实作答的证据**，只有回退证据；
5. "引用编号存在 ≠ 事实被支持"，需人工核对。

第 4 条尤其少见：主动承认"这部分我没证据"，比写"已全部验证"可信得多。

## 三条可操作建议（只是现象，供参考）

1. 演示脚本内置的三问里有两问（把字句、愚公移山）超出当前知识库，README 虽已注明"合格表现是未提及"，但演示时建议**先跑一问知识库内的数字题**（如"四级累计词汇量"），避免观众第一印象是"助手答不上来"。
2. README 的"在仓库根目录运行"可以删掉或改成"任意目录均可"——代码已按 `__file__` 算路径，说明白反而少一个坑。
3. `evidence/demo_run_20261109.json` 建议在 README 里给一行"怎么看这份证据"（哪个字段是 answer、哪个是 actual_engine），复核者不用点进去猜。

## 结论（只描述现象）

四维中：**Release / 已知限制 / README 复现**三项在远端可以直接核实且成立；**能不能跑**这一项，代码路径与异常兜底完整，但缺少对方环境的实跑证据。按"照着装能复现"的标准，这份仓库的说明足够让人自己装一遍。
