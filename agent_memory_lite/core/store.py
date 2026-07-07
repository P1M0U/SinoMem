"""记忆 CRUD 存储层（TTL 过期 + 重要性评分 + 结构化日志）"""

import contextlib
import json
import sqlite3
from datetime import UTC, datetime

from .logger import get_logger
from .tokenizer import tokenize

logger = get_logger(__name__)

# 内容最大长度（字符数），防止 LLM 写入超长文本导致搜索质量下降
MAX_CONTENT_LENGTH = 8000


def _parse_ttl(ttl: str | None) -> str | None:
    """将人类可读的 TTL 字符串转换为 ISO 时间戳

    支持格式: "30d"（天）, "24h"（小时）, "60m"（分钟）, "7d12h"
    返回 None 如果 ttl 为空或无效
    """
    if not ttl or not isinstance(ttl, str):
        return None

    import re

    units = {
        "d": 86400,
        "h": 3600,
        "m": 60,
    }
    total_seconds = 0
    for amount, unit in re.findall(r"(\d+)([dhm])", ttl.lower()):
        total_seconds += int(amount) * units[unit]

    if total_seconds <= 0:
        return None

    return (
        datetime.now(UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
        .replace("+00:00", "")
    )


def _iso_to_dt(ts: str | None):
    """将 ISO 时间戳转为 datetime（宽松解析）"""
    if not ts:
        return None
    try:
        # 尝试标准格式
        return datetime.fromisoformat(
            ts.replace("Z", "+00:00").replace(" ", "T")
        )
    except (ValueError, TypeError):
        return None


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
        skip_duplicate: bool = True,
        ttl: str | None = None,
        importance: float = 0.5,
    ) -> int:
        """存储一条记忆，返回 id

        Args:
            content: 记忆内容
            category: 分类
            tags: 标签列表
            skip_duplicate: 是否跳过重复内容（默认 True）
            ttl: 过期时间，如 "30d" / "24h" / "7d12h"（None 永不过期）
            importance: 重要性评分 0.0~1.0（默认 0.5）
        """
        if tags is None:
            tags = []

        # 校验内容长度：截断过长内容，防止搜索质量下降
        content = content.strip()
        if len(content) > MAX_CONTENT_LENGTH:
            content = content[:MAX_CONTENT_LENGTH]
            logger.warning("内容过长，已截断至 %d 字符", MAX_CONTENT_LENGTH)

        if not content:
            raise ValueError("内容不能为空")

        # 重要性范围校验
        importance = max(0.0, min(1.0, importance))

        # 解析 TTL
        expires_at = _parse_ttl(ttl)

        # 自动去重：检查是否已存在相同内容
        if skip_duplicate and self.exists_by_content(content):
            row = self.conn.execute(
                "SELECT id FROM memories WHERE content = ? LIMIT 1",
                (content,),
            ).fetchone()
            logger.info(
                "跳过重复内容 id=%d category=%s ttl=%s",
                row["id"],
                category,
                ttl or "none",
            )
            return row["id"]

        tags_json = json.dumps(tags, ensure_ascii=False)
        tokenized = tokenize(content)

        cursor = self.conn.execute(
            "INSERT INTO memories (content, category, tags, importance, "
            "expires_at) VALUES (?, ?, ?, ?, ?)",
            (content, category, tags_json, importance, expires_at),
        )
        row_id = cursor.lastrowid

        # FTS5 双写
        self.conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) "
            "VALUES (?, ?, ?, ?)",
            (row_id, tokenized, tags_json, category),
        )

        # 向量存储（仅向量模式下才 import numpy）
        if self._has_vec() and self._embedder:
            import numpy as np

            embedding = self._embedder.embed(content)
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            self.conn.execute(
                "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
                (row_id, embedding_bytes),
            )

        self.conn.commit()
        logger.info(
            "存储记忆 id=%d category=%s importance=%.2f ttl=%s",
            row_id,
            category,
            importance,
            ttl or "none",
        )
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
        importance: float | None = None,
        ttl: str | None = None,
    ) -> bool:
        """更新记忆（支持 importance 和 ttl 独立更新）"""
        existing = self.get(memory_id)
        if not existing:
            return False

        new_content = content if content is not None else existing["content"]
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
        new_importance = (
            importance
            if importance is not None
            else existing.get("importance", 0.5)
        )
        new_importance = max(0.0, min(1.0, new_importance))
        new_expires_at = (
            _parse_ttl(ttl) if ttl is not None else existing.get("expires_at")
        )
        tokenized = tokenize(new_content)

        self.conn.execute(
            "UPDATE memories SET content=?, category=?, tags=?, "
            "importance=?, expires_at=?, updated_at=CURRENT_TIMESTAMP "
            "WHERE id=?",
            (
                new_content,
                new_category,
                tags_json,
                new_importance,
                new_expires_at,
                memory_id,
            ),
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

        # 更新向量（仅向量模式下才 import numpy）
        if self._has_vec() and self._embedder and content is not None:
            import numpy as np

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
        logger.info("更新记忆 id=%d", memory_id)
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
        logger.info("删除记忆 id=%d", memory_id)
        return True

    def list_memories(
        self, category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """列出记忆（排除已过期的）"""
        if category:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE category=? AND "
                "(expires_at IS NULL OR expires_at > datetime('now')) "
                "ORDER BY importance DESC, created_at DESC LIMIT ?",
                (category, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM memories WHERE "
                "(expires_at IS NULL OR expires_at > datetime('now')) "
                "ORDER BY importance DESC, created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_dict(row) for row in rows]

    def stats(self) -> dict:
        """统计信息（含过期记忆数）"""
        total = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[
            0
        ]
        expired = self.conn.execute(
            "SELECT COUNT(*) FROM memories "
            "WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')"
        ).fetchone()[0]
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
            "expired": expired,
            "categories": {row["category"]: row["cnt"] for row in categories},
            "vectors": vec_count,
            "vector_enabled": self._has_vec(),
        }

    def cleanup_expired(self) -> int:
        """清理过期记忆，返回删除条数"""
        ids = [
            r["id"]
            for r in self.conn.execute(
                "SELECT id FROM memories "
                "WHERE expires_at IS NOT NULL AND expires_at <= datetime('now')"
            ).fetchall()
        ]

        if not ids:
            return 0

        placeholders = ",".join("?" * len(ids))
        self.conn.execute(
            f"DELETE FROM memories_fts WHERE rowid IN ({placeholders})",
            ids,
        )
        if self._has_vec():
            self.conn.execute(
                f"DELETE FROM memories_vec WHERE id IN ({placeholders})", ids
            )
        self.conn.execute(
            f"DELETE FROM memories WHERE id IN ({placeholders})", ids
        )
        self.conn.commit()
        logger.info("清理过期记忆: %d 条", len(ids))
        return len(ids)

    def reindex_fts(self) -> dict:
        """重新分词所有记忆并重建 FTS5 索引"""
        logger.info("重建 FTS5 索引...")
        memories = self.conn.execute(
            "SELECT id, content, tags, category FROM memories"
        ).fetchall()
        count = 0
        for mem in memories:
            tokenized = tokenize(mem["content"])
            self.conn.execute(
                "DELETE FROM memories_fts WHERE rowid=?", (mem["id"],)
            )
            self.conn.execute(
                "INSERT INTO memories_fts (rowid, content, tags, category) "
                "VALUES (?, ?, ?, ?)",
                (mem["id"], tokenized, mem["tags"], mem["category"]),
            )
            count += 1
        self.conn.commit()
        logger.info("FTS5 重建完成: %d 条", count)
        return {"reindexed": count}

    def exists_by_content(self, content: str) -> bool:
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

    def get_vec_dim(self) -> int | None:
        """获取现有向量表的维度（从 sqlite_master 解析 CREATE TABLE）"""
        import re

        if not self._has_vec():
            return None
        row = self.conn.execute(
            "SELECT sql FROM sqlite_master "
            "WHERE type='table' AND name='memories_vec'"
        ).fetchone()
        if not row:
            return None
        m = re.search(r"float\[(\d+)\]", row["sql"])
        return int(m.group(1)) if m else None

    def clear_vectors(self) -> int:
        """清空所有向量（用于强制重建）"""
        if not self._has_vec():
            return 0
        count = self.conn.execute(
            "SELECT COUNT(*) FROM memories_vec"
        ).fetchone()[0]
        self.conn.execute("DELETE FROM memories_vec")
        self.conn.commit()
        return count

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
        self.conn.execute("PRAGMA database_list")
        for row in self.conn.execute("PRAGMA database_list"):
            if row["name"] == "main":
                db_path = row["file"]
                break

        size_before = os.path.getsize(db_path) if db_path else 0
        self.conn.execute("VACUUM")
        size_after = os.path.getsize(db_path) if db_path else 0

        result = {
            "size_before": size_before,
            "size_after": size_after,
            "freed": size_before - size_after,
        }
        logger.info(
            "VACUUM: %.1f KB → %.1f KB (释放 %.1f KB)",
            size_before / 1024,
            size_after / 1024,
            (size_before - size_after) / 1024,
        )
        return result

    def delete_by_category(self, category: str) -> int:
        """按分类批量删除记忆，返回删除条数"""
        ids = [
            r["id"]
            for r in self.conn.execute(
                "SELECT id FROM memories WHERE category = ?", (category,)
            ).fetchall()
        ]

        if not ids:
            return 0

        placeholders = ",".join("?" * len(ids))
        self.conn.execute(
            f"DELETE FROM memories_fts WHERE rowid IN ({placeholders})",
            ids,
        )
        if self._has_vec():
            self.conn.execute(
                f"DELETE FROM memories_vec WHERE id IN ({placeholders})", ids
            )
        self.conn.execute(
            f"DELETE FROM memories WHERE id IN ({placeholders})", ids
        )
        self.conn.commit()
        logger.info("按分类删除: %s → %d 条", category, len(ids))
        return len(ids)

    def delete_all(self) -> int:
        """清空所有记忆"""
        count = self.conn.execute("SELECT COUNT(*) FROM memories").fetchone()[
            0
        ]
        self.conn.execute("DELETE FROM memories_fts")
        if self._has_vec():
            self.conn.execute("DELETE FROM memories_vec")
        self.conn.execute("DELETE FROM memories")
        self.conn.commit()
        logger.info("清空所有记忆: %d 条", count)
        return count
