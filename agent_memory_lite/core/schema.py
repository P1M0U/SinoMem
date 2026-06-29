"""数据库 schema 常量"""

# FTS5 tokenizer 说明：
# - jieba 预分词处理中文，写入 FTS5 前 content 已变为空格分隔的词语
# - unicode61 处理非中文部分（英文、数字等）
# - 不使用 content=memories 外部内容表，确保 jieba 分词结果真正写入 FTS5 索引
# - 写入和查询使用同一套 jieba 分词，token 完全对齐
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
    tokenize='unicode61'
);

CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_created ON memories(created_at);
"""


def vec_table_sql(vec_dim: int) -> str:
    """生成向量表 CREATE 语句（需要 sqlite-vec 扩展）"""
    return (
        "CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec USING vec0("
        "    id INTEGER PRIMARY KEY,"
        f"    embedding float[{vec_dim}]"
        ")"
    )
