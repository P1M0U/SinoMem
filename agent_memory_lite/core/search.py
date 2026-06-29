"""记忆搜索层（关键词 + 语义 + 混合）"""

import sqlite3

from .store import _row_to_dict, update_access
from .tokenizer import tokenize_for_fts5


class SearchEngine:
    """记忆搜索引擎"""

    def __init__(
        self,
        conn: sqlite3.Connection,
        embedder=None,
        vec_dim: int = 0,
    ):
        self.conn = conn
        self._embedder = embedder
        self._vec_dim = vec_dim

    def _has_vec(self) -> bool:
        """是否有向量表"""
        return self._vec_dim > 0

    def search(
        self,
        query: str,
        mode: str = "keyword",
        limit: int = 5,
        keyword_weight: float = 0.4,
    ) -> list[dict]:
        """搜索记忆

        Args:
            query: 搜索关键词
            mode: keyword（关键词）| semantic（语义）| hybrid（混合）
            limit: 返回条数
            keyword_weight: 混合模式下关键词权重（语义权重 = 1 - keyword_weight）
        """
        if mode == "semantic":
            return self._semantic_search(query, limit)
        elif mode == "hybrid":
            return self._hybrid_search(query, limit, keyword_weight)
        else:
            return self._keyword_search(query, limit)

    def _keyword_search(self, query: str, limit: int) -> list[dict]:
        """FTS5 关键词搜索（多词 AND 模式）"""
        # 存储时用空格分隔的 jieba 分词，查询时也用 AND 连接
        tokenized_query = tokenize_for_fts5(query)

        rows = self.conn.execute(
            """
            SELECT m.id, m.content, m.category, m.tags, m.created_at, rank
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (tokenized_query, limit),
        ).fetchall()

        update_access(self.conn, rows)
        return [
            _row_to_dict(row, score=round(1.0 / (1.0 + abs(row["rank"])), 4))
            for row in rows
        ]

    def _semantic_search(self, query: str, limit: int) -> list[dict]:
        """向量语义搜索"""
        if not self._has_vec() or not self._embedder:
            # 无向量索引，降级为关键词搜索
            return self._keyword_search(query, limit)

        query_embedding = self._embedder.embed(query)
        import numpy as np

        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        rows = self.conn.execute(
            """
            SELECT m.id, m.content, m.category, m.tags, m.created_at,
                   distance
            FROM memories_vec vec
            JOIN memories m ON m.id = vec.id
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
            """,
            (query_bytes, limit),
        ).fetchall()

        update_access(self.conn, rows)
        return [
            _row_to_dict(row, score=round(row["distance"], 4)) for row in rows
        ]

    def _hybrid_search(
        self, query: str, limit: int, keyword_weight: float
    ) -> list[dict]:
        """混合搜索（关键词 + 语义，score-based 加权排序）

        使用 score-based 归一化（而非 rank-based），保留实际分数差距：
        - keyword: 1/(1+|rank|)，rank 是 FTS5 的负 log 值
        - semantic: 1/(1+distance)
        """
        if not self._has_vec() or not self._embedder:
            return self._keyword_search(query, limit)

        # 获取更多候选（三倍），然后重新排序
        candidate_limit = limit * 3

        # 关键词搜索
        keyword_results = self._keyword_search_raw(query, candidate_limit)
        # 语义搜索
        semantic_results = self._semantic_search_raw(query, candidate_limit)

        # 合并去重，加权排序
        scores: dict[int, float] = {}
        results_map: dict[int, dict] = {}

        # 关键词结果打分（score-based）
        for r in keyword_results:
            rid = r["id"]
            # 使用 score 字段（已在 _keyword_search_raw 中计算）
            kw_score = r.get("score", 0)
            scores[rid] = scores.get(rid, 0) + kw_score * keyword_weight
            results_map[rid] = r

        # 语义结果打分（score-based）
        for r in semantic_results:
            rid = r["id"]
            sem_score = r.get("score", 0)
            scores[rid] = scores.get(rid, 0) + sem_score * (1 - keyword_weight)
            results_map[rid] = r

        # 按总分排序
        sorted_ids = sorted(
            scores.keys(), key=lambda x: scores[x], reverse=True
        )[:limit]

        update_access(
            self.conn,
            [results_map[rid] for rid in sorted_ids if rid in results_map],
        )

        return [
            {**results_map[rid], "score": round(scores[rid], 4)}
            for rid in sorted_ids
            if rid in results_map
        ]

    def _keyword_search_raw(self, query: str, limit: int) -> list[dict]:
        """关键词搜索（不更新访问计数）"""
        tokenized_query = tokenize_for_fts5(query)
        rows = self.conn.execute(
            """
            SELECT m.id, m.content, m.category, m.tags, m.created_at, rank
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (tokenized_query, limit),
        ).fetchall()
        return [
            _row_to_dict(row, score=round(1.0 / (1.0 + abs(row["rank"])), 4))
            for row in rows
        ]

    def _semantic_search_raw(self, query: str, limit: int) -> list[dict]:
        """语义搜索（不更新访问计数）"""
        if not self._has_vec() or not self._embedder:
            return []

        query_embedding = self._embedder.embed(query)
        import numpy as np

        query_bytes = np.array(query_embedding, dtype=np.float32).tobytes()

        rows = self.conn.execute(
            """
            SELECT m.id, m.content, m.category, m.tags, m.created_at, distance
            FROM memories_vec vec
            JOIN memories m ON m.id = vec.id
            WHERE embedding MATCH ? AND k = ?
            ORDER BY distance
            """,
            (query_bytes, limit),
        ).fetchall()
        return [
            _row_to_dict(row, score=round(1.0 / (1.0 + row["distance"]), 4))
            for row in rows
        ]
