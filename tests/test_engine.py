"""单元测试 — engine.py + embedder.py（Phase 2）"""


class TestStore:
    def test_store_returns_id(self, engine):
        mid = engine.store("用户偏好飞书发送文件")
        assert isinstance(mid, int)
        assert mid > 0

    def test_store_with_category(self, engine):
        mid = engine.store("用户喜欢 Python", category="user_pref")
        item = engine.get(mid)
        assert item["category"] == "user_pref"

    def test_store_with_tags(self, engine):
        mid = engine.store("MCP 协议笔记", tags=["mcp", "协议"])
        item = engine.get(mid)
        assert item["tags"] == ["mcp", "协议"]


class TestSearch:
    def test_search_chinese(self, engine):
        engine.store("用户偏好使用飞书发送文件")
        engine.store("服务器部署在阿里云")
        results = engine.search("飞书")
        assert len(results) >= 1
        assert "飞书" in results[0]["content"]

    def test_search_multi_word(self, engine):
        engine.store("用户喜欢 Python 编程")
        engine.store("用户使用 Vim 编辑器")
        results = engine.search("Python")
        assert len(results) >= 1
        assert "Python" in results[0]["content"]

    def test_search_empty(self, engine):
        results = engine.search("不存在的关键词xyz")
        assert results == []

    def test_search_limit(self, engine):
        for i in range(10):
            engine.store(f"记忆条目 {i} 关于测试")
        results = engine.search("测试", limit=3)
        assert len(results) <= 3

    def test_search_mode_keyword(self, engine):
        engine.store("飞书发送文件")
        results = engine.search("飞书", mode="keyword")
        assert len(results) >= 1


class TestSemanticSearch:
    """语义搜索测试（需要嵌入模型）"""

    def test_semantic_finds_related(self, engine_with_vec):
        """语义搜索能找到关键词不同但意思相近的内容"""
        engine_with_vec.store("用户偏好使用飞书发送文件")
        engine_with_vec.store("服务器部署在阿里云")
        # 搜"怎么给用户传东西" — 没有关键词匹配，但语义相近
        results = engine_with_vec.search("怎么给用户传东西", mode="semantic")
        assert len(results) >= 1
        assert "飞书" in results[0]["content"]

    def test_hybrid_search(self, engine_with_vec):
        """混合搜索同时考虑关键词和语义"""
        engine_with_vec.store("用户喜欢 Python 编程语言")
        engine_with_vec.store("用户偏好使用飞书发送文件")
        engine_with_vec.store("服务器部署在阿里云 ECS")
        results = engine_with_vec.search("Python", mode="hybrid")
        assert len(results) >= 1

    def test_semantic_degrades_without_model(self, engine):
        """无嵌入模型时语义搜索降级为关键词搜索"""
        engine.store("飞书发送文件")
        results = engine.search("飞书", mode="semantic")
        assert len(results) >= 1


class TestCRUD:
    def test_get_existing(self, engine):
        mid = engine.store("测试内容")
        item = engine.get(mid)
        assert item is not None
        assert item["content"] == "测试内容"

    def test_get_nonexistent(self, engine):
        assert engine.get(99999) is None

    def test_update_content(self, engine):
        mid = engine.store("旧内容")
        ok = engine.update(mid, content="新内容")
        assert ok is True
        assert engine.get(mid)["content"] == "新内容"

    def test_update_category(self, engine):
        mid = engine.store("测试", category="general")
        engine.update(mid, category="tool")
        assert engine.get(mid)["category"] == "tool"

    def test_delete_existing(self, engine):
        mid = engine.store("待删除")
        ok = engine.delete(mid)
        assert ok is True
        assert engine.get(mid) is None

    def test_delete_nonexistent(self, engine):
        assert engine.delete(99999) is False


class TestListAndStats:
    def test_list_all(self, engine):
        engine.store("a")
        engine.store("b")
        results = engine.list_memories()
        assert len(results) == 2

    def test_list_by_category(self, engine):
        engine.store("a", category="tool")
        engine.store("b", category="user_pref")
        results = engine.list_memories(category="tool")
        assert len(results) == 1
        assert results[0]["category"] == "tool"

    def test_stats(self, engine):
        engine.store("a", category="tool")
        engine.store("b", category="tool")
        engine.store("c", category="user_pref")
        s = engine.stats()
        assert s["total"] == 3
        assert s["categories"]["tool"] == 2
        assert s["categories"]["user_pref"] == 1
