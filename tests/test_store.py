"""测试 MemoryStore CRUD 操作"""

import pytest

from agent_memory_lite.engine import MemoryEngine


@pytest.fixture
def engine(tmp_path):
    """每个测试用例使用独立的临时数据库（无嵌入模型）"""
    db_path = tmp_path / "test_store.db"
    eng = MemoryEngine(db_path)
    yield eng
    eng.close()


class TestStoreCRUD:
    def test_store_and_get(self, engine):
        mid = engine.store("测试记忆内容")
        item = engine.get(mid)
        assert item is not None
        assert item["content"] == "测试记忆内容"
        assert item["category"] == "general"

    def test_update_content(self, engine):
        mid = engine.store("原始内容")
        ok = engine.update(mid, content="更新后内容")
        assert ok is True
        assert engine.get(mid)["content"] == "更新后内容"

    def test_update_category(self, engine):
        mid = engine.store("测试", category="general")
        ok = engine.update(mid, category="tool")
        assert ok is True
        assert engine.get(mid)["category"] == "tool"

    def test_delete(self, engine):
        mid = engine.store("待删除内容")
        ok = engine.delete(mid)
        assert ok is True
        assert engine.get(mid) is None

    def test_list_by_category(self, engine):
        engine.store("a", category="tool")
        engine.store("b", category="user_pref")
        engine.store("c", category="tool")
        results = engine.list_memories(category="tool")
        assert len(results) == 2
        assert all(r["category"] == "tool" for r in results)

    def test_stats(self, engine):
        engine.store("a", category="tool")
        engine.store("b", category="tool")
        engine.store("c", category="user_pref")
        s = engine.stats()
        assert s["total"] == 3
        assert s["categories"]["tool"] == 2
        assert s["categories"]["user_pref"] == 1

    def test_exists_by_content(self, engine):
        engine.store("独一无二的内容")
        assert engine.exists_by_content("独一无二的内容") is True
        assert engine.exists_by_content("不存在的内容") is False
