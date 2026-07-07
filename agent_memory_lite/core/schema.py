"""数据库 schema 常量与迁移管理"""

# FTS5 tokenizer 说明：
# - jieba 预分词处理中文，写入 FTS5 前 content 已变为空格分隔的词语
# - unicode61 处理非中文部分（英文、数字等）
# - 不使用 content=memories 外部内容表，确保 jieba 分词结果真正写入 FTS5 索引
# - 写入和查询使用同一套 jieba 分词，token 完全对齐
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    tags TEXT DEFAULT '[]',
    importance REAL DEFAULT 0.5,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INTEGER DEFAULT 0,
    last_accessed TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
    content,
    tags,
    category,
    tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_memories_expires ON memories(expires_at);
"""

# 当前数据库 schema 版本号
SCHEMA_VERSION = 1


def vec_table_sql(vec_dim: int) -> str:
    """生成向量表 CREATE 语句（需要 sqlite-vec 扩展）"""
    return (
        "CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0("
        "    id INTEGER PRIMARY KEY,"
        f"    embedding float[{vec_dim}]"
        ")"
    )


def run_migrations(conn) -> None:
    """运行 schema 迁移，确保数据库处于最新版本

    迁移链：
        v0 → v1: 新增 importance / expires_at 字段 + schema_version 表
    """
    # 查询当前版本
    try:
        row = conn.execute(
            "SELECT MAX(version) FROM schema_version"
        ).fetchone()
        current = row[0] if row and row[0] is not None else 0
    except Exception:
        current = 0

    if current < 1:
        # v1 迁移: 新增字段 + schema_version 表
        _migrate_v1(conn)
        current = 1

    if current < SCHEMA_VERSION:
        conn.execute(
            "INSERT INTO schema_version (version) VALUES (?)",
            (SCHEMA_VERSION,),
        )
        conn.commit()


def _migrate_v1(conn) -> None:
    """v0 → v1: 新增 importance 和 expires_at 字段（如果不存在则添加）"""
    import logging

    logger = logging.getLogger("agent_memory_lite")
    logger.info("运行数据库迁移 v0 → v1...")

    # 检查重要性字段
    cols = {
        r["name"]
        for r in conn.execute("PRAGMA table_info(memories)").fetchall()
    }
    if "importance" not in cols:
        conn.execute(
            "ALTER TABLE memories ADD COLUMN importance REAL DEFAULT 0.5"
        )
    if "expires_at" not in cols:
        conn.execute("ALTER TABLE memories ADD COLUMN expires_at TIMESTAMP")

    # 创建过期时间索引（如果不存在）
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_memories_expires "
        "ON memories(expires_at)"
    )

    # 创建 schema_version 表（如果尚未存在）
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)"
    )
    conn.execute("INSERT INTO schema_version (version) VALUES (1)")
    conn.commit()
    logger.info("数据库迁移 v0 → v1 完成")
