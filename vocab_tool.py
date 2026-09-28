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
            
            # 3. 写入文件
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