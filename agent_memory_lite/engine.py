"""SQLite 存储 + FTS5 中文搜索 + 向量语义搜索"""

import json
import sqlite3
from pathlib import Path
from typing import Optional

import numpy as np

from .tokenizer import tokenize

DEFAULT_DB_PATH = Path.home() / ".agent-memory" / "memory.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    tags,
    category,
    content=memories,
    content_rowid=id,
    tokenize='unicode61 remove_diacritics 2'
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
"""


class MemoryEngine:
    """记忆存储与搜索引擎（Phase 2: FTS5 + 向量 + 混合搜索）"""

    def __init__(self, db_path: Optional[str | Path] = None, embedder=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._embedder = embedder
        self._vec_dim: int = 0
        self._init_schema()
        self._init_vec()

    def _init_schema(self):
        """初始化 FTS5 表结构"""
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()

    def _init_vec(self):
        """初始化 sqlite-vec 向量表（如果 embedder 可用）"""
        if self._embedder is None:
            return
        try:
            import sqlite_vec

            self.conn.enable_load_extension(True)
            sqlite_vec.load(self.conn)
            self.conn.enable_load_extension(False)
        except Exception:
            # sqlite-vec 不可用，跳过向量功能
            return

        self._vec_dim = self._embedder.dim

        # 创建向量表
        self.conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0(
                id INTEGER PRIMARY KEY,
                embedding float[{self._vec_dim}]
            )
            """
        )
        self.conn.commit()

    def _has_vec(self) -> bool:
        """是否有向量表"""
        return self._vec_dim > 0

    def store(
        self, content: str, category: str = "general", tags: Optional[list[str]] = None
    ) -> int:
        """存储一条记忆，返回 id"""
        if tags is None:
            tags = []
        tags_json = json.dumps(tags, ensure_ascii=False)
        tokenized = tokenize(content)

        cursor = self.conn.execute(
            "INSERT INTO memories (content, category, tags) VALUES (?, ?, ?)",
            (content, category, tags_json),
        )
        row_id = cursor.lastrowid

        # FTS5 双写
        self.conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) VALUES (?, ?, ?, ?)",
            (row_id, tokenized, tags_json, category),
        )

        # 向量存储
        if self._has_vec() and self._embedder:
            embedding = self._embedder.embed(content)
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            self.conn.execute(
                "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
                (row_id, embedding_bytes),
            )

        self.conn.commit()
        return row_id

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
        """FTS5 关键词搜索"""
        tokenized_query = tokenize(query)

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

        self._update_access(rows)
        return [self._row_to_dict(row, score=abs(row["rank"])) for row in rows]

    def _semantic_search(self, query: str, limit: int) -> list[dict]:
        """向量语义搜索"""
        if not self._has_vec() or not self._embedder:
            # 无向量索引，降级为关键词搜索
            return self._keyword_search(query, limit)

        query_embedding = self._embedder.embed(query)
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

        self._update_access(rows)
        return [self._row_to_dict(row, score=row["distance"]) for row in rows]

    def _hybrid_search(
        self, query: str, limit: int, keyword_weight: float
    ) -> list[dict]:
        """混合搜索（关键词 + 语义加权排序）"""
        if not self._has_vec() or not self._embedder:
            return self._keyword_search(query, limit)

        # 获取更多候选（双倍），然后重新排序
        candidate_limit = limit * 3

        # 关键词搜索
        keyword_results = self._keyword_search_raw(query, candidate_limit)
        # 语义搜索
        semantic_results = self._semantic_search_raw(query, candidate_limit)

        # 合并去重，加权排序
        scores: dict[int, float] = {}
        results_map: dict[int, dict] = {}

        # 关键词结果打分
        for i, r in enumerate(keyword_results):
            rid = r["id"]
            # 归一化分数：排名越靠前分越高
            kw_score = 1.0 - (i / max(len(keyword_results), 1))
            scores[rid] = scores.get(rid, 0) + kw_score * keyword_weight
            results_map[rid] = r

        # 语义结果打分
        for i, r in enumerate(semantic_results):
            rid = r["id"]
            sem_score = 1.0 - (i / max(len(semantic_results), 1))
            scores[rid] = scores.get(rid, 0) + sem_score * (1 - keyword_weight)
            results_map[rid] = r

        # 按总分排序
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[
            :limit
        ]

        self._update_access(
            [results_map[rid] for rid in sorted_ids if rid in results_map]
        )

        return [
            {**results_map[rid], "score": scores[rid]}
            for rid in sorted_ids
            if rid in results_map
        ]

    def _keyword_search_raw(self, query: str, limit: int) -> list[dict]:
        """关键词搜索（不更新访问计数）"""
        tokenized_query = tokenize(query)
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
        return [self._row_to_dict(row, score=abs(row["rank"])) for row in rows]

    def _semantic_search_raw(self, query: str, limit: int) -> list[dict]:
        """语义搜索（不更新访问计数）"""
        if not self._has_vec() or not self._embedder:
            return []

        query_embedding = self._embedder.embed(query)
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
        return [self._row_to_dict(row, score=row["distance"]) for row in rows]

    def _update_access(self, rows):
        """批量更新访问计数"""
        for row in rows:
            self.conn.execute(
                "UPDATE memories SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
                (row["id"],),
            )
        self.conn.commit()

    def get(self, memory_id: int) -> Optional[dict]:
        """获取指定记忆"""
        row = self.conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def update(
        self,
        memory_id: int,
        content: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> bool:
        """更新记忆"""
        existing = self.get(memory_id)
        if not existing:
            return False

        new_content = content if content is not None else existing["content"]
        new_category = category if category is not None else existing["category"]
        new_tags = tags if tags is not None else existing["tags"]
        tags_json = (
            json.dumps(new_tags, ensure_ascii=False)
            if isinstance(new_tags, list)
            else new_tags
        )
        tokenized = tokenize(new_content)

        self.conn.execute(
            "UPDATE memories SET content=?, category=?, tags=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_content, new_category, tags_json, memory_id),
        )
        # 更新 FTS5
        self.conn.execute("DELETE FROM memories_fts WHERE rowid=?", (memory_id,))
        self.conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) VALUES (?, ?, ?, ?)",
            (memory_id, tokenized, tags_json, new_category),
        )

        # 更新向量
        if self._has_vec() and self._embedder:
            embedding = self._embedder.embed(new_content)
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            self.conn.execute("DELETE FROM memories_vec WHERE id=?", (memory_id,))
            self.conn.execute(
                "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
                (memory_id, embedding_bytes),
            )

        self.conn.commit()
        return True

    def delete(self, memory_id: int) -> bool:
        """删除记忆"""
        existing = self.get(memory_id)
        if not existing:
            return False

        self.conn.execute("DELETE FROM memories_fts WHERE rowid=?", (memory_id,))
        if self._has_vec():
            self.conn.execute("DELETE FROM memories_vec WHERE id=?", (memory_id,))
        self.conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        self.conn.commit()
        return True

    def list_memories(self, category: str = None, limit: int = 20) -> list[dict]:
        """列出记忆"""
        if category:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE category=? ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    def stats(self) -> dict:
        """统计信息"""
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        categories = self.conn.execute(
            "SELECT category, COUNT(*) as cnt FROM memories GROUP BY category ORDER BY cnt DESC"
        ).fetchall()
        vec_count = 0
        if self._has_vec():
            vec_count = self.conn.execute(
                "SELECT COUNT(*) FROM memories_vec"
            ).fetchone()[0]
        return {
            "total": total,
            "categories": {row["category"]: row["cnt"] for row in categories},
            "vectors": vec_count,
            "vector_enabled": self._has_vec(),
        }

    def _row_to_dict(self, row, score: Optional[float] = None) -> dict:
        """将 sqlite3.Row 转为 dict"""
        d = dict(row)
        if "tags" in d and d["tags"]:
            try:
                d["tags"] = json.loads(d["tags"])
            except (json.JSONDecodeError, TypeError):
                pass
        if score is not None:
            d["score"] = round(score, 4)
        return d

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
