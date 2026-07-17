"""MCP Server 入口 — Agent 通过 stdin/stdout 调用"""

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from ..core.engine import MemoryEngine, create_engine

_engine: MemoryEngine | None = None


@lifespan
async def engine_lifespan(server):
    """管理 MemoryEngine 生命周期：启动时创建，退出时 close"""
    global _engine
    _engine = create_engine()
    yield
    if _engine:
        _engine.close()
        _engine = None


mcp = FastMCP("agent-memory-lite", lifespan=engine_lifespan)


def _get_engine() -> MemoryEngine:
    """获取引擎实例（仅 lifespan 初始化后可用）"""
    global _engine
    if _engine is None:
        raise RuntimeError(
            "引擎尚未初始化，请确保 MCP Server 通过 lifespan 启动"
        )
    return _engine


@mcp.tool()
def store_memory(
    content: str,
    category: str = "general",
    tags: list[str] | None = None,
    skip_duplicate: bool = True,
    ttl: str | None = None,
    importance: float = 0.5,
) -> dict:
    """存储一条记忆

    Args:
        content: 记忆内容
        category: 分类 (user_pref, project, tool, general)
        tags: 标签列表
        skip_duplicate: 是否跳过重复内容（默认 True）
        ttl: 过期时间，如 "30d" / "24h" / "7d12h"（None 永不过期）
        importance: 重要性评分 0.0~1.0（默认 0.5）
    """
    if tags is None:
        tags = []
    engine = _get_engine()
    memory_id = engine.store(
        content,
        category,
        tags,
        skip_duplicate,
        ttl=ttl,
        importance=importance,
    )
    return {"id": memory_id, "status": "ok"}


@mcp.tool()
def search_memory(
    query: str, mode: str = "keyword", limit: int = 5
) -> list[dict]:
    """搜索记忆（支持 keyword / semantic / hybrid 三种模式）

    keyword: BM25 关键词匹配
    semantic: 向量语义相似度
    hybrid: RRF 排名融合（无需手动加权）

    Args:
        query: 搜索关键词
        mode: keyword（关键词BM25）| semantic（语义）| hybrid（RRF融合）
        limit: 返回条数
    """
    engine = _get_engine()
    return engine.search(query, mode=mode, limit=limit)


@mcp.tool()
def get_memory(memory_id: int) -> dict | None:
    """获取指定 id 的记忆

    Args:
        memory_id: 记忆 id
    """
    engine = _get_engine()
    return engine.get(memory_id)


@mcp.tool()
def update_memory(
    memory_id: int,
    content: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    importance: float | None = None,
    ttl: str | None = None,
) -> dict:
    """更新记忆内容/分类/标签/重要性/过期时间

    Args:
        memory_id: 记忆 id
        content: 新内容（None 表示不改）
        category: 新分类（None 表示不改）
        tags: 新标签（None 表示不改）
        importance: 重要性 0.0~1.0（None 表示不改）
        ttl: 过期时间 30d/24h/7d12h（None 表示不改）
    """
    engine = _get_engine()
    ok = engine.update(
        memory_id,
        content=content,
        category=category,
        tags=tags,
        importance=importance,
        ttl=ttl,
    )
    return {"status": "ok" if ok else "not_found"}


@mcp.tool()
def delete_memory(memory_id: int) -> dict:
    """删除指定 id 的记忆

    Args:
        memory_id: 记忆 id
    """
    engine = _get_engine()
    ok = engine.delete(memory_id)
    return {"status": "ok" if ok else "not_found"}


@mcp.tool()
def delete_memories_by_category(category: str) -> dict:
    """按分类批量删除记忆

    Args:
        category: 要删除的分类
    """
    engine = _get_engine()
    count = engine.delete_by_category(category)
    return {"status": "ok", "deleted": count}


@mcp.tool()
def reindex_memories() -> dict:
    """重新分词并重建 FTS5 索引（词典更新后使用）"""
    engine = _get_engine()
    result = engine.reindex_fts()
    return {"status": "ok", "reindexed": result["reindexed"]}


@mcp.tool()
def cleanup_memories() -> dict:
    """清理所有已过期的记忆"""
    engine = _get_engine()
    count = engine.cleanup_expired()
    return {"status": "ok", "cleaned": count}


@mcp.tool()
def store_memories_batch(
    items: list[dict],
    skip_duplicate: bool = True,
) -> dict:
    """批量存储多条记忆（单事务）

    Args:
        items: [{"content": "...", "category": "general", "tags": [],
                  "ttl": "30d", "importance": 0.5}, ...]
        skip_duplicate: 是否跳过重复内容
    """
    engine = _get_engine()
    ids = engine.store_batch(items, skip_duplicate=skip_duplicate)
    return {"ids": ids, "count": len(ids), "status": "ok"}


@mcp.tool()
def search_memories_batch(
    queries: list[dict],
) -> list[list[dict]]:
    """批量搜索（共享模型加载）

    Args:
        queries: [{"query": "...", "mode": "keyword", "limit": 5}, ...]
    """
    engine = _get_engine()
    return engine.search_batch(queries)


@mcp.tool()
def list_memories(category: str | None = None, limit: int = 20) -> list[dict]:
    """列出记忆（按重要性排序，排除过期）

    Args:
        category: 按分类过滤（None 返回全部）
        limit: 返回条数
    """
    engine = _get_engine()
    return engine.list_memories(category=category, limit=limit)


@mcp.tool()
def memory_stats() -> dict:
    """查看记忆统计信息（含过期记忆数）"""
    engine = _get_engine()
    return engine.stats()


@mcp.tool()
def vacuum_memory() -> dict:
    """回收已删除记忆占用的磁盘空间（VACUUM）"""
    engine = _get_engine()
    return engine.vacuum()


@mcp.tool()
def delete_all_memories() -> dict:
    """清空所有记忆（⚠️ 不可逆操作）"""
    engine = _get_engine()
    count = engine.delete_all()
    return {"status": "ok", "deleted": count}


if __name__ == "__main__":
    mcp.run()
