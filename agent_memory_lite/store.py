"""记忆 CRUD 存储层"""

import contextlib
import json
import sqlite3

import numpy as np

from .tokenizer import tokenize

# 内容最大长度（字符数），防止 LLM 写入超长文本导致搜索质量下降
MAX_CONTENT_LENGTH = 8000


def _row_to_dict(row, score: float | None = None) -> dict:
    """将 sqlite3.Row 转为 dict，解析 tags JSON"""
    d = dict(row)
    if "tags" in d and d["tags"]:
        with contextlib.suppress(json.JSONDecodeError, TypeError):
            d["tags"] = json.loads(d["tags"])
    if score is not None:
        d["score"] = round(score, 4)
    return d


def update_access(conn: sqlite3.Connection, rows: list) -> None:
    """批量更新访问计数（模块级函数，供 MemoryStore 和 SearchEngine 共用）"""
    for row in rows:
        conn.execute(
            "UPDATE memories SET access_count = access_count + 1, "
            "last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
            (row["id"],),
        )
    conn.commit()


class MemoryStore:
    """记忆 CRUD 操作"""

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

    def store(
        self,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> int:
        """存储一条记忆，返回 id"""
        if tags is None:
            tags = []

        # 校验内容长度：截断过长内容，防止搜索质量下降
        content = content.strip()
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]

        if not content:
            raise ValueError("内容不能为空")

        tags_json = json.dumps(tags, ensure_ascii=False)
        tokenized = tokenize(content)

        cursor = self.conn.execute(
            "INSERT INTO memories (content, category, tags) VALUES (?, ?, ?)",
            (content, category, tags_json),
        )
        row_id = cursor.lastrowid

        # FTS5 双写
        self.conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) "
            "VALUES (?, ?, ?, ?)",
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

    def get(self, memory_id: int) -> dict | None:
        """获取指定记忆"""
        row = self.conn.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        return _row_to_dict(row) if row else None

    def update(
        self,
        memory_id: int,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """更新记忆（三表同步：memories + memories_fts + memories_vec）"""
        existing = self.get(memory_id)
        if not existing:
            return False

        new_content = content if content is not None else existing["content"]
        # 截断过长内容
        new_content = new_content.strip()
        if len(new_content) > MAX_CONTENT_LENGTH:
            new_content = new_content[:MAX_CONTENT_LENGTH]
        if not new_content:
            raise ValueError("内容不能为空")
        new_category = (
            category if category is not None else existing["category"]
        )
        new_tags = tags if tags is not None else existing["tags"]
        tags_json = (
            json.dumps(new_tags, ensure_ascii=False)
            if isinstance(new_tags, list)
            else new_tags
        )
        tokenized = tokenize(new_content)

        self.conn.execute(
            "UPDATE memories SET content=?, category=?, tags=?, "
            "updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (new_content, new_category, tags_json, memory_id),
        )
        # 更新 FTS5
        self.conn.execute(
            "DELETE FROM memories_fts WHERE rowid=?", (memory_id,)
        )
        self.conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) "
            "VALUES (?, ?, ?, ?)",
            (memory_id, tokenized, tags_json, new_category),
        )

        # 更新向量
        if self._has_vec() and self._embedder:
            embedding = self._embedder.embed(new_content)
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            self.conn.execute(
                "DELETE FROM memories_vec WHERE id=?", (memory_id,)
            )
            self.conn.execute(
                "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
                (memory_id, embedding_bytes),
            )

        self.conn.commit()
        return True

    def delete(self, memory_id: int) -> bool:
        """删除记忆（三表同步）"""
        existing = self.get(memory_id)
        if not existing:
            return False

        self.conn.execute(
            "DELETE FROM memories_fts WHERE rowid=?", (memory_id,)
        )
        if self._has_vec():
            self.conn.execute(
                "DELETE FROM memories_vec WHERE id=?", (memory_id,)
            )
        self.conn.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        self.conn.commit()
        return True

    def list_memories(
        self, category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """列出记忆"""
        if category:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE category=? "
                "ORDER BY created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def stats(self) -> dict:
        """统计信息"""
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[
            0
        ]
        categories = self.conn.execute(
            "SELECT category, COUNT(*) as cnt FROM memories "
            "GROUP BY category ORDER BY cnt DESC"
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

    def exists_by_content(self, content: str) -> bool:
        """检查是否已存在相同内容的记忆"""
        row = self.conn.execute(
            "SELECT 1 FROM memories WHERE content = ? LIMIT 1", (content,)
        ).fetchone()
        return row is not None

    def get_vector_ids(self) -> set[int]:
        """获取已有向量的记忆 ID 集合"""
        if not self._has_vec():
            return set()
        rows = self.conn.execute("SELECT id FROM memories_vec").fetchall()
        return {r["id"] for r in rows}

    def add_vector(self, memory_id: int, embedding_bytes: bytes) -> None:
        """为已有记忆添加向量"""
        if not self._has_vec():
            return
        self.conn.execute(
            "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
            (memory_id, embedding_bytes),
        )
        self.conn.commit()

    def vacuum(self) -> dict:
        """回收已删除空间，返回数据库文件大小（字节）变化"""
        import os

        db_path = None
        # 查找数据库文件路径
        self.conn.execute("PRAGMA database_list")
        for row in self.conn.execute("PRAGMA database_list"):
            if row["name"] == "main":
                db_path = row["file"]
                break

        size_before = os.path.getsize(db_path) if db_path else 0
        self.conn.execute("VACUUM")
        size_after = os.path.getsize(db_path) if db_path else 0

        return {
            "size_before": size_before,
            "size_after": size_after,
            "freed": size_before - size_after,
        }
