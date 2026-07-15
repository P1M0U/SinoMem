"""记忆搜索层（关键词 + 语义 + 混合，RRF 融合）"""

import sqlite3

from .logger import get_logger, timed
from .store import _row_to_dict, update_access
from .tokenizer import tokenize_for_fts5

logger = get_logger(__name__)

# RRF 融合常数，典型取值 60（文献推荐）
RRF_K = 60


class SearchEngine:
    """记忆搜索引擎（BM25 关键词 + 语义向量 + RRF 混合融合）"""

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
    ) -> list[dict]:
        """搜索记忆

        Args:
            query: 搜索关键词
            mode: keyword（关键词BM25）| semantic（语义）| hybrid（RRF混合）
            limit: 返回条数
        """
        if mode == "semantic":
            return self._semantic_search(query, limit)
        elif mode == "hybrid":
            return self._hybrid_rrf_search(query, limit)
        else:
            return self._keyword_search(query, limit)

    # ── P1: 关键词搜索（BM25 排序）──

    def _keyword_search(self, query: str, limit: int) -> list[dict]:
        """BM25 关键词搜索（多词 AND 模式）"""
        with timed(logger, f"keyword_search(limit={limit})"):
            return self._keyword_search_raw(query, limit, update=True)

    # ── 语义搜索 ──

    def _semantic_search(self, query: str, limit: int) -> list[dict]:
        """向量语义搜索"""
        with timed(logger, f"semantic_search(limit={limit})"):
            if not self._has_vec() or not self._embedder:
                logger.info("semantic 降级为 keyword（无向量表或模型）")
                return self._keyword_search(query, limit)
            return self._semantic_search_raw(query, limit, update=True)

    # ── P1: RRF 混合搜索 ──

    def _hybrid_rrf_search(self, query: str, limit: int) -> list[dict]:
        """RRF（Reciprocal Rank Fusion）混合搜索

        对关键词和语义两路结果分别按排名归一化后合并排序，
        消除两路得分的量纲不一致问题。

        公式: RRF(d) = sum(1 / (K + rank_i(d))) for each list i
        """
        with timed(logger, "hybrid_rrf_search"):
            if not self._has_vec() or not self._embedder:
                logger.info("hybrid 降级为 keyword（无向量表或模型）")
                return self._keyword_search(query, limit)

            rrf_limit = limit * 3

            # 两路各自搜索
            kw_results = self._keyword_search_raw(
                query, rrf_limit, update=False
            )
            sem_results = self._semantic_search_raw(
                query, rrf_limit, update=False
            )

            # RRF 排名融合: RRF(d) = 1/(K+rank) for each list
            rrf_scores: dict[int, float] = {}
            results_map: dict[int, dict] = {}

            # 关键词排名（排名从 1 开始）
            for rank, r in enumerate(kw_results, start=1):
                rid = r["id"]
                rrf_scores[rid] = rrf_scores.get(rid, 0) + 1.0 / (RRF_K + rank)
                results_map[rid] = r

            # 语义排名
            for rank, r in enumerate(sem_results, start=1):
                rid = r["id"]
                rrf_scores[rid] = rrf_scores.get(rid, 0) + 1.0 / (RRF_K + rank)
                if rid not in results_map:
                    results_map[rid] = r

            # 按 RRF 得分排序
            sorted_ids = sorted(
                rrf_scores.keys(),
                key=lambda x: rrf_scores[x],
                reverse=True,
            )[:limit]

            update_access(
                self.conn,
                [results_map[rid] for rid in sorted_ids if rid in results_map],
            )

            return [
                {**results_map[rid], "score": round(rrf_scores[rid], 4)}
                for rid in sorted_ids
                if rid in results_map
            ]

    # ── 内部方法（不更新访问计数）──

    def _keyword_search_raw(
        self, query: str, limit: int, update: bool = False
    ) -> list[dict]:
        """关键词搜索（使用 BM25 排序）"""
        tokenized_query = tokenize_for_fts5(query)

        # 使用 bm25() 替代 rank 获得更好的排序质量
        rows = self.conn.execute(
            """
            SELECT m.id, m.content, m.category, m.tags, m.created_at,
                   bm25(memories_fts) AS rank
            FROM memories_fts fts
            JOIN memories m ON m.id = fts.rowid
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (tokenized_query, limit),
        ).fetchall()

        if update:
            update_access(self.conn, rows)

        return [
            _row_to_dict(row, score=round(1.0 / (1.0 + abs(row["rank"])), 4))
            for row in rows
        ]

    def _semantic_search_raw(
        self, query: str, limit: int, update: bool = False
    ) -> list[dict]:
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

        if update:
            update_access(self.conn, rows)

        return [
            _row_to_dict(row, score=round(1.0 / (1.0 + row["distance"]), 4))
            for row in rows
        ]

    def search_batch(
        self,
        queries: list[dict],
    ) -> list[dict]:
        """批量搜索（共享模型加载），返回每个 query 的结果列表

        Args:
            queries: [{"query": "...", "mode": "keyword", "limit": 5}, ...]

        每个 query 项的 mode 默认为 "keyword"，limit 默认为 5
        """
        results = []
        for q in queries:
            query = q["query"]
            mode = q.get("mode", "keyword")
            limit = q.get("limit", 5)
            results.append(self.search(query, mode=mode, limit=limit))

        logger.info("批量搜索完成: %d 个查询", len(queries))
        return results
