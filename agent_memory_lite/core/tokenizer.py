"""jieba 中文分词封装 — cut 精确模式 + token 内部 bigram 扩展

jieba 采用惰性加载：首次调用 tokenize() 时才初始化词典和缓存，
避免无关路径（如纯 CLI 统计查询）也触发 ~0.6s 冷启动开销。
"""

import re
from pathlib import Path

# ── 路径配置（纯路径操作，不触发 jieba 加载）──

# 将 jieba 缓存目录指向用户可写位置，避免多用户 /tmp 冲突
_CACHE_DIR = Path.home() / ".cache" / "jieba"

# 自定义词典路径
_DICT_PATH = Path(__file__).parent.parent / "dicts" / "tech_terms.txt"

# 匹配 CJK 字符，用于判断是否对 token 做 bigram 扩展
_CJK_RE = re.compile(r"[一-鿿]")

# 惰性初始化标记
_jieba_initialized = False


def _init_jieba():
    """惰性初始化 jieba（词典 + 缓存 + 自定义词库）

    只在首次实际需要分词时才触发，避免模块导入时即加载 ~0.6s。
    """
    global _jieba_initialized
    if _jieba_initialized:
        return

    import jieba

    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    jieba.dt.tmp_dir = str(_CACHE_DIR)

    if _DICT_PATH.exists():
        jieba.load_userdict(str(_DICT_PATH))

    # 将 jieba 注入模块全局，后续调用直接使用
    globals()["jieba"] = jieba
    _jieba_initialized = True


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
    _init_jieba()
    words = list(jieba.cut(text))  # type: ignore[name-defined]  # noqa: F821
    return " ".join(_expand_bigrams(words))


def tokenize_list(text: str) -> list[str]:
    """jieba 精确分词，返回词语列表（用于调试/展示）"""
    _init_jieba()
    return list(jieba.cut(text))  # type: ignore[name-defined]  # noqa: F821


def tokenize_for_fts5(query: str) -> str:
    """将多关键词查询转为 FTS5 AND 语法

    写入和查询用同一套管道（cut + bigram）确保 token 对齐。
    """
    _init_jieba()
    expanded = _expand_bigrams(
        jieba.cut(query)  # type: ignore[name-defined]  # noqa: F821
    )
    # 去重保序（存储侧已同时写入完整词 + bigram，查询侧无需过滤长词）
    words = list(dict.fromkeys([w for w in expanded if w.strip()]))
    if not words:
        # 兜底：全部被过滤了（如纯英文长词），退回到原始 cut
        words = [
            w
            for w in jieba.cut(query)  # type: ignore[name-defined]  # noqa: F821
            if w.strip()
        ]
    if not words:
        return ""
    # 统一用双引号包裹，避免 FTS5 单搜索词触发前缀匹配
    return " AND ".join(f'"{w}"' for w in words)
