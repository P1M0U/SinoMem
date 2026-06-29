"""SQLite 存储 + FTS5 中文搜索 + 向量语义搜索"""

import sqlite3
from pathlib import Path

from .config import DEFAULT_DB_PATH
from .schema import SCHEMA_SQL, vec_table_sql
from .search import SearchEngine
from .store import MemoryStore


class MemoryEngine:
    """记忆存储与搜索引擎（门面类，组合 MemoryStore + SearchEngine）"""

    def __init__(self, db_path: str | Path | None = None, embedder=None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._embedder = embedder
        self._vec_dim: int = 0
        self._init_schema()
        self._init_vec()

        self._store = MemoryStore(self.conn, embedder, self._vec_dim)
        self._search = SearchEngine(self.conn, embedder, self._vec_dim)

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
            # sqlite-vec 不可用（打包环境/ARM/扩展禁用），跳过向量功能
            return

        try:
            self._vec_dim = self._embedder.dim
        except Exception:
            # 嵌入模型加载失败（文件缺失/损坏），降级为纯 FTS5
            self._embedder = None
            return

        # 创建向量表
        try:
            self.conn.execute(vec_table_sql(self._vec_dim))
            self.conn.commit()
        except Exception:
            # 向量表创建失败，降级
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
    ) -> int:
        """存储一条记忆，返回 id（默认跳过重复内容）"""
        return self._store.store(content, category, tags, skip_duplicate)

    def search(
        self,
        query: str,
        mode: str = "keyword",
        limit: int = 5,
        keyword_weight: float = 0.4,
    ) -> list[dict]:
        """搜索记忆"""
        return self._search.search(query, mode, limit, keyword_weight)

    def get(self, memory_id: int) -> dict | None:
        """获取指定记忆"""
        return self._store.get(memory_id)

    def update(
        self,
        memory_id: int,
        content: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        """更新记忆"""
        return self._store.update(memory_id, content, category, tags)

    def delete(self, memory_id: int) -> bool:
        """删除记忆"""
        return self._store.delete(memory_id)

    def list_memories(
        self, category: str | None = None, limit: int = 20
    ) -> list[dict]:
        """列出记忆"""
        return self._store.list_memories(category, limit)

    def stats(self) -> dict:
        """统计信息"""
        return self._store.stats()

    def exists_by_content(self, content: str) -> bool:
        """检查是否已存在相同内容的记忆"""
        return self._store.exists_by_content(content)

    def get_vector_ids(self) -> set[int]:
        """获取已有向量的记忆 ID 集合"""
        return self._store.get_vector_ids()

    def add_vector(self, memory_id: int, embedding_bytes: bytes) -> None:
        """为已有记忆添加向量"""
        self._store.add_vector(memory_id, embedding_bytes)

    def vacuum(self) -> dict:
        """回收已删除空间，返回数据库文件大小变化"""
        return self._store.vacuum()

    def delete_by_category(self, category: str) -> int:
        """按分类批量删除记忆，返回删除条数"""
        return self._store.delete_by_category(category)

    def delete_all(self) -> int:
        """清空所有记忆，返回删除条数"""
        return self._store.delete_all()

    def reindex_fts(self) -> dict:
        """重新分词所有记忆并重建 FTS5 索引"""
        return self._store.reindex_fts()

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def create_engine(
    db_path: str | Path | None = None,
    model_dir: str | Path | None = None,
) -> MemoryEngine:
    """统一创建 MemoryEngine，自动处理 Embedder 降级"""
    embedder = None
    try:
        from .embedder import Embedder

        embedder = Embedder(model_dir)
        # 主动触发模型加载（Embedder 是懒加载的，.dim 才真正加载）
        # 放在 try 内，加载失败则降级为纯 FTS5 模式
        _ = embedder.dim
    except Exception:
        embedder = None

    try:
        return MemoryEngine(db_path, embedder=embedder)
    except Exception:
        # MemoryEngine 构造失败时也降级
        if embedder is not None:
            embedder = None
            return MemoryEngine(db_path, embedder=embedder)
        raise
