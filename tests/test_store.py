"""测试 MemoryStore CRUD 操作"""

import pytest

from agent_memory_lite.core.engine import MemoryEngine


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

    def test_store_empty_content_raises(self, engine):
        """空内容应抛出 ValueError"""
        with pytest.raises(ValueError, match="内容不能为空"):
            engine.store("")
        with pytest.raises(ValueError, match="内容不能为空"):
            engine.store("   ")

    def test_store_truncates_long_content(self, engine):
        """超过 8000 字的内容应被截断"""
        long_content = "测试" * 5000  # 10000 字 > 8000
        mid = engine.store(long_content)
        item = engine.get(mid)
        assert len(item["content"]) <= 8000

    def test_store_dedup(self, engine):
        """默认跳过重复内容"""
        mid1 = engine.store("相同内容")
        mid2 = engine.store("相同内容")
        assert mid1 == mid2  # 返回相同 id

    def test_store_allow_duplicate(self, engine):
        """允许重复时创建新记录"""
        mid1 = engine.store("相同内容")
        mid2 = engine.store("相同内容", skip_duplicate=False)
        assert mid1 != mid2  # 不同 id

    def test_delete_by_category(self, engine):
        """按分类批量删除"""
        engine.store("a", category="test-cat")
        engine.store("b", category="test-cat")
        engine.store("c", category="other")
        count = engine.delete_by_category("test-cat")
        assert count == 2
        assert engine.list_memories(category="test-cat") == []

    def test_delete_all(self, engine):
        """清空所有记忆"""
        engine.store("a")
        engine.store("b")
        engine.store("c")
        count = engine.delete_all()
        assert count == 3
        assert engine.stats()["total"] == 0

    def test_reindex_fts(self, engine):
        """FTS5 重建索引"""
        engine.store("测试重新分词")  # noqa: B018
        result = engine.reindex_fts()
        assert result["reindexed"] >= 1
