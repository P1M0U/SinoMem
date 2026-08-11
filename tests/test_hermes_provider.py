"""Hermes MemoryProvider 适配器测试

SinoMemProvider 在非 Hermes 环境使用占位基类，方法均为自实现，
因此可在无 Hermes 运行时下直接测试核心逻辑（工具处理、自动同步）。
"""

import json

import pytest

from sinomem.core.engine import MemoryEngine


@pytest.fixture
def provider(monkeypatch, tmp_path):
    """创建 SinoMemProvider 实例（monkeypatch _create_engine 避免模型探测）"""
    from sinomem.plugins.hermes import provider as mod

    def fake_create(db_path=None, model_dir=None, with_embedder=True):
        return MemoryEngine(db_path)

    monkeypatch.setattr(mod, "_create_engine", fake_create)
    p = mod.SinoMemProvider()
    p.initialize("test-session", db_path=str(tmp_path / "m.db"))
    yield p
    p.shutdown()


class TestHermesProvider:
    def test_store_and_search(self, provider):
        """memory_store 写入后 memory_search 可检索"""
        rid = json.loads(
            provider.handle_tool_call(
                "memory_store",
                {"content": "用户喜欢飞书", "category": "user_pref"},
            )
        )
        results = json.loads(
            provider.handle_tool_call("memory_search", {"query": "飞书"})
        )
        assert results
        assert results[0]["id"] == rid
        assert results[0]["content"] == "用户喜欢飞书"

    def test_memory_list_filter(self, provider):
        """memory_list 支持按分类过滤"""
        provider.handle_tool_call("memory_store", {"content": "条目A"})
        provider.handle_tool_call(
            "memory_store", {"content": "条目B", "category": "tool"}
        )
        items = json.loads(
            provider.handle_tool_call("memory_list", {"category": "tool"})
        )
        assert len(items) == 1
        assert items[0]["content"] == "条目B"

    def test_unknown_tool_returns_error(self, provider):
        """未知工具返回 error 信息"""
        r = provider.handle_tool_call("no_such_tool", {})
        assert "error" in r or "未知工具" in r

    def test_on_memory_write_syncs(self, provider):
        """内置 memory 工具写入自动镜像到 SinoMem（核心卖点）"""
        provider.on_memory_write(
            "add",
            "memory",
            "自动同步的内容",
            {"category": "user_pref", "tags": ["t1"]},
        )
        items = json.loads(provider.handle_tool_call("memory_list", {}))
        assert any("自动同步的内容" in i["content"] for i in items)

    def test_skip_writes_non_primary(self, monkeypatch, tmp_path):
        """非主上下文（subagent/cron）不镜像写入"""
        from sinomem.plugins.hermes import provider as mod

        def fake_create(db_path=None, model_dir=None, with_embedder=True):
            return MemoryEngine(db_path)

        monkeypatch.setattr(mod, "_create_engine", fake_create)
        p = mod.SinoMemProvider()
        p.initialize(
            "s",
            db_path=str(tmp_path / "m.db"),
            agent_context="subagent",
        )
        try:
            assert p._skip_writes is True
            p.on_memory_write("add", "memory", "不应写入的内容", {})
            items = json.loads(p.handle_tool_call("memory_list", {}))
            assert all("不应写入" not in i["content"] for i in items)
        finally:
            p.shutdown()

    def test_get_tool_schemas(self, provider):
        """暴露 3 个工具 schema"""
        names = [s["name"] for s in provider.get_tool_schemas()]
        assert names == ["memory_search", "memory_store", "memory_list"]

    def test_system_prompt_block(self, provider):
        """系统提示块包含记忆统计"""
        provider.handle_tool_call("memory_store", {"content": "统计测试"})
        block = provider.system_prompt_block()
        assert "SinoMem" in block
        assert "1 memories" in block
