"""jieba 中文分词封装"""

from pathlib import Path

import jieba

# 加载自定义词典（如果存在）
_DICT_PATH = Path(__file__).parent.parent / "dicts" / "tech_terms.txt"
if _DICT_PATH.exists():
    jieba.load_userdict(str(_DICT_PATH))


def tokenize(text: str) -> str:
    """jieba 分词，返回空格分隔的词语"""
    return " ".join(jieba.cut(text))


def tokenize_list(text: str) -> list[str]:
    """jieba 分词，返回词语列表"""
    return list(jieba.cut(text))


def tokenize_for_fts5(query: str) -> str:
    """将多关键词查询转为 FTS5 AND 语法

    默认 FTS5 将空格分隔解释为短语匹配，这里用 * 加回 AND：
    "飞书 文件" → '"飞书" AND "文件"'
    """
    words = [w for w in jieba.cut(query) if w.strip()]
    if len(words) <= 1:
        return " ".join(words)
    # 每个词加双引号，用 AND 连接（FTS5 enhanced query syntax）
    return " AND ".join(f'"{w}"' for w in words)
