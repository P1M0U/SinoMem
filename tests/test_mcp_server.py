"""测试 MCP Server 工具函数（不需要启动 MCP 进程）"""

import pytest

from agent_memory_lite.core.engine import MemoryEngine
from agent_memory_lite.entrypoints.mcp_server import (
    delete_memory,
    get_memory,
    list_memories,
    memory_stats,
    search_memories_batch,
    search_memory,
    store_memories_batch,
    store_memory,
    update_memory,
)


@pytest.fixture(autouse=True)
def setup_engine(tmp_path, monkeypatch):
    """每个测试使用独立的临时数据库"""
    db_path = tmp_path / "test_mcp.db"
    engine = MemoryEngine(str(db_path))

    # 注入 engine 到 mcp_server 模块
    monkeypatch.setattr(
        "agent_memory_lite.entrypoints.mcp_server._get_engine", lambda: engine
    )
    yield engine
    engine.close()


class TestMCPTools:
    def test_store_memory_tool(self, setup_engine):
        result = store_memory("MCP 测试记忆", category="tool")
        assert result["id"] > 0
        assert result["status"] == "ok"

    def test_search_memory_tool(self, setup_engine):
        store_memory("飞书发送文件", category="tool")
        store_memory("Python 编程", category="user_pref")
        results = search_memory("飞书")
        assert len(results) >= 1
        assert any("飞书" in r["content"] for r in results)

    def test_get_memory_tool(self, setup_engine):
        result = store_memory("获取测试")
        mid = result["id"]
        item = get_memory(mid)
        assert item is not None
        assert item["content"] == "获取测试"

    def test_update_memory_tool(self, setup_engine):
        result = store_memory("旧内容")
        mid = result["id"]
        res = update_memory(mid, content="新内容")
        assert res["status"] == "ok"
        item = get_memory(mid)
        assert item["content"] == "新内容"

    def test_delete_memory_tool(self, setup_engine):
        result = store_memory("待删除")
        mid = result["id"]
        res = delete_memory(mid)
        assert res["status"] == "ok"
        assert get_memory(mid) is None

    def test_list_memories_tool(self, setup_engine):
        store_memory("a", category="tool")
        store_memory("b", category="user_pref")
        results = list_memories()
        assert len(results) == 2

    def test_memory_stats_tool(self, setup_engine):
        store_memory("a", category="tool")
        store_memory("b", category="tool")
        s = memory_stats()
        assert s["total"] == 2
        assert s["categories"]["tool"] == 2

    def test_store_memories_batch_tool(self, setup_engine):
        """批量存储 MCP 工具"""
        items = [
            {"content": "批量 MCP A", "category": "tool"},
            {"content": "批量 MCP B", "importance": 0.9},
        ]
        result = store_memories_batch(items)
        assert result["status"] == "ok"
        assert result["count"] == 2
        assert len(result["ids"]) == 2

    def test_search_memories_batch_tool(self, setup_engine):
        """批量搜索 MCP 工具"""
        store_memory("飞书", category="tool")
        store_memory("Docker", category="tool")
        queries = [{"query": "飞书"}, {"query": "不存在"}]
        results = search_memories_batch(queries)
        assert len(results) == 2
        assert len(results[0]) >= 1
        assert results[1] == []
