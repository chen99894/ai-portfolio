# AI辅助编程实修录

## 1. 任务与提示词
**要做什么：** 基于已有的 `vocab_tool.py` 脚本（读取生词表CSV -> 筛选HSK4 -> 生成造句练习），扩展一个新功能：生成填空题。

**我写的提示词：**
 帮我根据我现在写的代码，扩展一个生成填空题的功能。具体要求：
新增一个函数，读取 HSK4 的词汇，把词汇所在的例句（如果没有例句就用默认模板）中的目标词汇挖空变成 `______`。 把生成的填空题写入到 `填空练习.txt` 中。先给我完整代码，然后再解释怎么修改。

## 2. AI 初版代码
*(以下为AI第一次给出的完整生成填空题的代码，尚未经过我后期修改)*

```python
def gen_fill_in_blanks(words, out=None):
    out = out or "填空练习.txt"
    with open(out, "w", encoding="utf-8") as f:
        for w in words:
            word = w["词汇"]
            pos = w["词性"]
            # AI初始逻辑：强行读取“例句”列，没有容错
            example_sentence = w["例句"] 
            blanked_sentence = example_sentence.replace(word, "______")
            f.write(f"请填空：{blanked_sentence} （提示：{pos}）\n")
            f.write(f"答案：{word}\n\n")
    return out

3. 我的修改点
① 修改了路径解析逻辑。 把 out = "填空练习.txt" 改成了 out = weekpath.root_path("填空练习.txt")。
② 增加了字典读取的容错处理。 把 w["例句"] 改成了 w.get("例句", 默认模板)。
③ 优化了输出文件的格式。 把 f.write(f"请填空：...") 改成了分行的 【填空题】、【提示】、【答案】 结构。
④ 使用 f-string 替代了 % 格式化输出。 把主程序中打印统计信息的 % 写法改成了 f-string。

4. 最终版 vs 初版差异说明
  AI最开始写乱了 "填空练习.txt"，如果用户在其他目录运行 Python 脚本，文件就会乱跑。后来参照原脚本中 weekpath.root_path() 的用法进行了修正。
  不够严谨： AI 默认我的 CSV 里一定有“例句”这一列。但我的 CSV 其实不一定有，如果直接运行 w["例句"] 程序会报错崩溃。所以用了 w.get("例句", 默认模板)，这是让代码更健壮。
    我修改的原因： AI 写的文本挤在一行。为了打印出来做练习更清晰，我改成了三段式排版，并加上了 【提示】。

最终版
python
# W3 生词表 CSV -> 自动生成练习题
# 运行: python vocab_tool.py
import os
import csv
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import weekpath  # noqa: E402 统一解析 data/ 路径，换目录也不会找不到文件

DATA = weekpath.data_path("生词表.csv")

def load_words(path=DATA):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))

def filter_by_level(words, level="4"):
    return [w for w in words if str(w["HSK等级"]) == str(level)]

def count_by_pos(words):
    d = {}
    for w in words:
        d[w["词性"]] = d.get(w["词性"], 0) + 1
    return d

def gen_exercises(words, out=None):
    # 产物统一落到代码包根目录；否则“从哪个目录运行”决定了文件落在哪，
    # 与 README 的“任意目录运行”承诺冲突，且散落的产物 .gitignore 拦不住。
    out = out or weekpath.root_path("练习.txt")
    with open(out, "w", encoding="utf-8") as f:
        for w in words:
            f.write("用“%s”造一个句子。 (%s)\n" % (w["词汇"], w["词性"]))
    return out

# ================= 新增：作业2 - 生成填空题 =================
def gen_fill_in_blanks(words, out=None):
    """
    生成填空题：把例句中的目标词汇挖空。
    这里假设 CSV 表里有 '例句' 列。如果没有，会自动使用默认模板。
    """
    out = out or weekpath.root_path("填空练习.txt")
    with open(out, "w", encoding="utf-8") as f:
        for w in words:
            word = w["词汇"]
            pos = w["词性"]
            
            # 1. 尝试获取 CSV 中的“例句”列，如果没有则使用默认模板
            # 你可以根据你实际的 CSV 表头，把 "例句" 改成实际的名字
            example_sentence = w.get("例句", f"我喜欢学习关于{pos}的词汇：{word}。")
            
            # 2. 挖空逻辑：把例句中出现的目标词汇替换成下划线
            blanked_sentence = example_sentence.replace(word, "______")
            
            # 3. 写入文件，做格式化排版
            f.write(f"【填空题】请填入合适的词汇：{blanked_sentence}\n")
            f.write(f"【提示】词性：{pos}\n")
            f.write(f"【答案】{word}\n\n")
            
    return out
# ==========================================================

if __name__ == "__main__":
    words = load_words()
    lv4 = filter_by_level(words, "4")
    
    # 作业1：使用 f-string 替代 % 格式化输出，更简洁易读
    print(f"总词汇 {len(words)} 个，其中 HSK4 词汇 {len(lv4)} 个，词性分布: {count_by_pos(lv4)}")
    
    # 生成造句练习 (原有功能)
    out = weekpath.root_path("练习.txt")
    gen_exercises(lv4, out)
    print(f"已生成造句练习: {out}")
    
    # 生成填空练习 (作业2新增功能)
    blank_out = weekpath.root_path("填空练习.txt")
    gen_fill_in_blanks(lv4, blank_out)
    print(f"已生成填空练习: {blank_out}")
