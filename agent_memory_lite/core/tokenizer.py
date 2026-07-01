"""jieba 中文分词封装"""

from pathlib import Path

import jieba

# 加载自定义词典（如果存在）
_DICT_PATH = Path(__file__).parent.parent.parent / "dicts" / "tech_terms.txt"
if _DICT_PATH.exists():
    jieba.load_userdict(str(_DICT_PATH))


def tokenize(text: str) -> str:
    """jieba 细粒度分词，返回空格分隔的词语"""
    return " ".join(jieba.cut_for_search(text))


def tokenize_list(text: str) -> list[str]:
    """jieba 分词，返回词语列表"""
    return list(jieba.cut(text))


def tokenize_for_fts5(query: str) -> str:
    """将多关键词查询转为 FTS5 AND 语法

    写入和查询都用 cut_for_search 确保 token 对齐，
    过滤 ≤3 字的 token 避免 cut_for_search 产出的长子串
    在存储侧不存在时导致的 false negative。
    """
    # 去重保序：cut_for_search 会产生重复token
    words = list(
        dict.fromkeys(
            [
                w
                for w in jieba.cut_for_search(query)
                if w.strip() and len(w) <= 3
            ]
        )
    )
    if not words:
        # 兜底：如果全部被过滤了，用原始 cut
        words = [w for w in jieba.cut(query) if w.strip()]
    if len(words) <= 1:
        return " ".join(words)
    return " AND ".join(f'"{w}"' for w in words)
