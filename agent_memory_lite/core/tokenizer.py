"""jieba 中文分词封装 — cut 精确模式 + token 内部 bigram 扩展"""

import re
from pathlib import Path

import jieba

# 加载自定义词典（如果存在）
_DICT_PATH = Path(__file__).parent.parent.parent / "dicts" / "tech_terms.txt"
if _DICT_PATH.exists():
    jieba.load_userdict(str(_DICT_PATH))

# 匹配 CJK 字符，用于判断是否对 token 做 bigram 扩展
_CJK_RE = re.compile(r"[一-鿿]")


def _expand_bigrams(words: list[str]) -> list[str]:
    """对 >=3 字的中文 token 做内部 bigram 扩展

    cut 精确模式只产出完整词，但 FTS5 需要子串来提升召回率。
    只在 token 内部做 bigram（不跨 token 边界），
    避免 cut_for_search 跨词边界产生的假词。
    非中文 token 保持不变。
    """
    result = []
    for w in words:
        if len(w) >= 3 and _CJK_RE.match(w[0]):
            result.append(w)
            for i in range(len(w) - 1):
                result.append(w[i : i + 2])
        else:
            result.append(w)
    return result


def tokenize(text: str) -> str:
    """精确分词 + bigram 扩展，返回空格分隔的词语（用于写入 FTS5 索引）"""
    words = list(jieba.cut(text))
    return " ".join(_expand_bigrams(words))


def tokenize_list(text: str) -> list[str]:
    """jieba 精确分词，返回词语列表（用于调试/展示）"""
    return list(jieba.cut(text))


def tokenize_for_fts5(query: str) -> str:
    """将多关键词查询转为 FTS5 AND 语法

    写入和查询用同一套管道（cut + bigram）确保 token 对齐。
    """
    expanded = _expand_bigrams(jieba.cut(query))
    # 去重保序（存储侧已同时写入完整词 + bigram，查询侧无需过滤长词）
    words = list(dict.fromkeys([w for w in expanded if w.strip()]))
    if not words:
        # 兜底：全部被过滤了（如纯英文长词），退回到原始 cut
        words = [w for w in jieba.cut(query) if w.strip()]
    if len(words) <= 1:
        return " ".join(words)
    return " AND ".join(f'"{w}"' for w in words)
