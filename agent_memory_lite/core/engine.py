"""SQLite 存储 + FTS5 中文搜索 + 向量语义搜索"""

import sqlite3
from pathlib import Path

from .config import DEFAULT_DB_PATH
from .logger import get_logger
from .schema import SCHEMA_SQL, SCHEMA_VERSION, run_migrations, vec_table_sql
from .search import SearchEngine
from .store import MemoryStore

logger = get_logger(__name__)


class MemoryEngine:
    """记忆存储与搜索引擎（门面类，组合 MemoryStore + SearchEngine）"""

    def __init__(self, db_path: str | Path | None = None, embedder=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(
            str(self.db_path), check_same_thread=False
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._embedder = embedder
        self._vec_dim: int = 0
        self._init_schema()
        self._init_vec()
        # 运行迁移
        run_migrations(self._conn)

        self._store = MemoryStore(self._conn, embedder, self._vec_dim)
        self._search = SearchEngine(self._conn, embedder, self._vec_dim)

        logger.info(
            "MemoryEngine 初始化完成 db=%s vec=%s schema_version=%d",
            self.db_path,
            "enabled" if self._has_vec() else "disabled",
            SCHEMA_VERSION,
        )

    def _init_schema(self):
        """初始化 FTS5 表结构"""
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def _init_vec(self):
        """初始化 sqlite-vec 向量表（如果 embedder 可用）"""
        if self._embedder is None:
            return
        try:
            import sqlite_vec

            self._conn.enable_load_extension(True)
            sqlite_vec.load(self._conn)
            self._conn.enable_load_extension(False)
        except Exception:
            logger.warning("sqlite-vec 加载失败，跳过向量功能")
            return

        try:
            self._vec_dim = self._embedder.dim
        except Exception:
            logger.warning("嵌入模型加载失败，降级为纯 FTS5")
            self._embedder = None
            return

        try:
            self._conn.execute(vec_table_sql(self._vec_dim))
            self._conn.commit()
            logger.info("向量表创建成功 dim=%d", self._vec_dim)
        except Exception:
            logger.warning("向量表创建失败，降级为纯 FTS5")
            self._vec_dim = 0
            self._embedder = None

    def _has_vec(self) -> bool:
        """是否有向量表"""
        return self._vec_dim > 0

    # ── 公开 API（透传到子对象）──

    def store(
        self,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
        skip_duplicate: bool = True,
        ttl: str | None = None,
        importance: float = 0.5,
    ) -> int:
        """存储一条记忆，返回 id（默认跳过重复内容）

        Args:
            ttl: 过期时间，如 "30d" / "24h" / "7d12h"
            importance: 重要性 0.0~1.0
        """
        return self._store.store(
            content,
            category,
            tags,
            skip_duplicate,
            ttl=ttl,
            importance=importance,
        )

    def search(
        self,
        query: str,
        mode: str = "keyword",
        limit: int = 5,
    ) -> list[dict]:
        """搜索记忆（keyword: BM25, hybrid: RRF 融合）"""
        return self._search.search(query, mode, limit)

    def get(self, memory_id: int) -> dict | None:
        """获取指定记忆"""
        return self._store.get(memory_id)

    def update(
        self,
        memory_id: int,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        importance: float | None = None,
        ttl: str | None = None,
    ) -> bool:
        """更新记忆"""
        return self._store.update(
            memory_id,
            content,
            category,
            tags,
            importance=importance,
            ttl=ttl,
        )

    def delete(self, memory_id: int) -> bool:
        """删除记忆"""
        return self._store.delete(memory_id)

    def list_memories(
        self, category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """列出记忆（排除过期）"""
        return self._store.list_memories(category, limit)

    def stats(self) -> dict:
        """统计信息"""
        return self._store.stats()

    def cleanup_expired(self) -> int:
        """清理过期记忆"""
        return self._store.cleanup_expired()

    def exists_by_content(self, content: str) -> bool:
        """检查是否已存在相同内容的记忆"""
        return self._store.exists_by_content(content)

    def get_vector_ids(self) -> set[int]:
        """获取已有向量的记忆 ID 集合"""
        return self._store.get_vector_ids()

    def get_vec_dim(self) -> int | None:
        """获取现有向量表的维度"""
        return self._store.get_vec_dim()

    def add_vector(self, memory_id: int, embedding_bytes: bytes) -> None:
        """为已有记忆添加向量"""
        self._store.add_vector(memory_id, embedding_bytes)

    def vacuum(self) -> dict:
        """回收已删除空间"""
        return self._store.vacuum()

    def delete_by_category(self, category: str) -> int:
        """按分类批量删除记忆"""
        return self._store.delete_by_category(category)

    def clear_vectors(self) -> int:
        """清空所有向量（公共 API，供 migrate 等使用）"""
        return self._store.clear_vectors()

    def embed_batch(self, texts: list[str]) -> list[list[float]] | None:
        """批量文本嵌入（公共 API，供 migrate 等使用）

        Returns:
            嵌入向量列表，如果嵌入模型不可用返回 None
        """
        if self._embedder is None:
            return None
        return self._embedder.embed_batch(texts)

    @property
    def embedder_dim(self) -> int | None:
        """嵌入模型维度（None 表示不可用）"""
        return self._vec_dim if self._has_vec() else None

    def get_embedder_dim(self) -> int | None:
        """获取嵌入模型维度（None 表示不可用）"""
        if self._embedder is None:
            return None
        return self._vec_dim

    def delete_all(self) -> int:
        """清空所有记忆"""
        return self._store.delete_all()

    def reindex_fts(self) -> dict:
        """重新分词所有记忆并重建 FTS5 索引"""
        return self._store.reindex_fts()

    def store_batch(
        self, items: list[dict], skip_duplicate: bool = True
    ) -> list[int]:
        """批量存储记忆（单事务），返回 id 列表"""
        return self._store.store_batch(items, skip_duplicate)

    def search_batch(self, queries: list[dict]) -> list[dict]:
        """批量搜索（共享模型加载）"""
        return self._search.search_batch(queries)

    def close(self):
        """关闭数据库连接"""
        self._conn.close()
        logger.info("MemoryEngine 已关闭")

    def store_with_expiry(
        self,
        content: str,
        already_expired: bool = True,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> int:
        """写入指定过期状态的记忆（供测试使用）

        绕过 TTL 解析和重复检查，仅应在测试场景中使用。

        Args:
            content: 记忆内容
            already_expired: True 写入已过期的记忆（默认）
            category: 分类
            tags: 标签列表

        Returns:
            新记忆的 id
        """
        import json

        if tags is None:
            tags = []
        tags_json = json.dumps(tags, ensure_ascii=False)

        from .tokenizer import tokenize

        # 使用参数化查询，根据 already_expired 构造过期时间
        if already_expired:
            expires_sql = "datetime('now', '-1 day')"
        else:
            expires_sql = "datetime('now', '+30 days')"

        cursor = self._conn.execute(
            "INSERT INTO memories (content, category, tags, expires_at) "
            "VALUES (?, ?, ?, " + expires_sql + ")",
            (content, category, tags_json),
        )
        row_id = cursor.lastrowid

        self._conn.execute(
            "INSERT INTO memories_fts (rowid, content, tags, category) "
            "VALUES (?, ?, ?, ?)",
            (row_id, tokenize(content), tags_json, category),
        )
        self._conn.commit()
        return row_id

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def create_engine(
    db_path: str | Path | None = None,
    model_dir: str | Path | None = None,
) -> MemoryEngine:
    """统一创建 MemoryEngine，自动处理 Embedder 降级与模型下载"""
    embedder = None
    try:
        from .embedder import Embedder, ensure_model

        # 模型缺失时尝试自动下载
        ensure_model(model_dir)

        embedder = Embedder(model_dir)
        _ = embedder.dim
    except Exception as e:
        logger.warning("嵌入模型加载失败，降级为纯 FTS5 搜索: %s", e)
        embedder = None

    try:
        return MemoryEngine(db_path, embedder=embedder)
    except Exception as e:
        if embedder is not None:
            logger.warning(
                "创建引擎失败（embedder 相关），降级为纯 FTS5: %s", e
            )
            embedder = None
            return MemoryEngine(db_path, embedder=embedder)
        raise
