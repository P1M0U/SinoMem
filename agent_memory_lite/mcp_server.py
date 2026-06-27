"""MCP Server 入口 — Agent 通过 stdin/stdout 调用"""

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from .engine import MemoryEngine, create_engine

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
    """获取引擎实例（lazy init 兜底）"""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


@mcp.tool()
def store_memory(
    content: str, category: str = "general", tags: list[str] = None
) -> dict:
    """存储一条记忆

    Args:
        content: 记忆内容
        category: 分类 (user_pref, project, tool, general)
        tags: 标签列表
    """
    if tags is None:
        tags = []
    engine = _get_engine()
    memory_id = engine.store(content, category, tags)
    return {"id": memory_id, "status": "ok"}


@mcp.tool()
def search_memory(
    query: str, mode: str = "keyword", limit: int = 5
) -> list[dict]:
    """搜索记忆（支持 keyword / semantic / hybrid 三种模式）

    Args:
        query: 搜索关键词
        mode: keyword（关键词匹配）| semantic（语义相似）| hybrid（混合排序）
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
    content: str = "",
    category: str = "",
    tags: list[str] = None,
) -> dict:
    """更新记忆内容/分类/标签

    Args:
        memory_id: 记忆 id
        content: 新内容（留空不改）
        category: 新分类（留空不改）
        tags: 新标签（留空不改）
    """
    if tags is None:
        tags = []
    engine = _get_engine()
    ok = engine.update(
        memory_id,
        content=content or None,
        category=category or None,
        tags=tags or None,
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
def list_memories(category: str = "", limit: int = 20) -> list[dict]:
    """列出记忆

    Args:
        category: 按分类过滤（留空返回全部）
        limit: 返回条数
    """
    engine = _get_engine()
    return engine.list_memories(category=category or None, limit=limit)


@mcp.tool()
def memory_stats() -> dict:
    """查看记忆统计信息"""
    engine = _get_engine()
    return engine.stats()


if __name__ == "__main__":
    mcp.run()
