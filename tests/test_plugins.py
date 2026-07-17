"""插件层 + 边界情况测试"""

import tempfile
from pathlib import Path


class TestBasePlugin:
    """BasePlugin 核心功能测试"""

    def test_create_plugin(self):
        """create_plugin 工厂函数"""
        from agent_memory_lite.plugins import create_plugin

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            plugin = create_plugin(db_path=db)
            assert plugin is not None
            assert str(db) in repr(plugin)
            plugin.close()

    def test_auto_store_and_search(self):
        """auto_store 存储后 auto_search 能找到"""
        from agent_memory_lite.plugins import create_plugin

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            plugin = create_plugin(db_path=db)

            mid = plugin.auto_store(
                "用户偏好使用飞书进行团队协作", category="user_pref"
            )
            assert mid > 0

            results = plugin.auto_search("飞书", mode="keyword", limit=5)
            assert len(results) > 0
            assert any("飞书" in r["content"] for r in results)

            plugin.close()

    def test_auto_store_dedup(self):
        """auto_store 默认去重"""
        from agent_memory_lite.plugins import create_plugin

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            plugin = create_plugin(db_path=db)

            mid1 = plugin.auto_store("测试去重", category="general")
            mid2 = plugin.auto_store("测试去重", category="general")
            assert mid1 == mid2

            plugin.close()

    def test_inject_context(self):
        """inject_context 将记忆注入到 prompt"""
        from agent_memory_lite.plugins import create_plugin

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            plugin = create_plugin(db_path=db)

            keyword = "ai-memory-test-keyword"
            plugin.auto_store(f"用户偏好 {keyword}", category="user_pref")

            # 搜索这个唯一关键词
            enhanced = plugin.inject_context(keyword, mode="keyword", limit=3)
            assert keyword in enhanced

            plugin.close()

    def test_empty_search_returns_empty(self):
        """空数据库搜索返回空列表"""
        from agent_memory_lite.plugins import create_plugin

        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.db"
            plugin = create_plugin(db_path=db)
            results = plugin.auto_search("不存在的关键词")
            assert results == []
            plugin.close()


class TestTokenizer:
    """分词边界情况测试"""

    def test_tokenize_long_chinese(self):
        """四字及以上中文词不被过滤"""
        from agent_memory_lite.core.tokenizer import (
            tokenize,
            tokenize_for_fts5,
        )

        text = "自然语言处理是重要技术方向"
        tokenized = tokenize(text)

        # bigram 扩展后确保子串存在
        assert "自然" in tokenized
        assert "语言" in tokenized
        assert "处理" in tokenized

        # 查询端不自我设限
        fts5_query = tokenize_for_fts5("自然语言处理")
        assert len(fts5_query) > 0
        assert "自然语言处理" not in fts5_query  # jieba 切为 2-2-2

    def test_tokenize_mixed_content(self):
        """混合中英文分词"""
        from agent_memory_lite.core.tokenizer import tokenize

        text = "用户使用 Docker 部署 Python 应用"
        result = tokenize(text)
        assert "Docker" in result
        assert "Python" in result
        assert "部署" in result

    def test_tokenize_for_fts5_multi_word(self):
        """多词查询转为 AND 语法"""
        from agent_memory_lite.core.tokenizer import tokenize_for_fts5

        result = tokenize_for_fts5("飞书 协作")
        assert " AND " in result
        assert "飞书" in result


class TestTTL:
    """TTL 过期测试"""

    def test_parse_ttl_valid(self):
        """有效的 TTL 字符串解析"""
        from agent_memory_lite.core.store import _parse_ttl

        result_30d = _parse_ttl("30d")
        assert result_30d is not None
        assert "T" in result_30d

        result_24h = _parse_ttl("24h")
        assert result_24h is not None

        result_mixed = _parse_ttl("7d12h")
        assert result_mixed is not None

    def test_parse_ttl_invalid(self):
        """无效 TTL 返回 None"""
        from agent_memory_lite.core.store import _parse_ttl

        assert _parse_ttl(None) is None
        assert _parse_ttl("") is None
        assert _parse_ttl("abc") is None
        assert _parse_ttl("0d") is None
        assert _parse_ttl(123) is None  # type: ignore — 测试非字符串

    def test_ttl_expired_memory(self):
        """过期记忆可被清理"""
        from agent_memory_lite.core.engine import MemoryEngine

        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "test.db")
            engine = MemoryEngine(db)

            # 使用 store_with_expiry 写入已过期的记忆
            row_id = engine.store_with_expiry(
                "已过期的记忆",
                already_expired=True,
            )

            # 清理过期
            cleaned = engine.cleanup_expired()
            assert cleaned >= 1
            assert row_id > 0

            engine.close()


class TestConfig:
    """配置测试"""

    def test_config_no_dead_code(self):
        """确认无用配置项已移除"""
        from agent_memory_lite.core import config

        assert not hasattr(config, "DEFAULT_KEYWORD_WEIGHT")
        assert not hasattr(config, "DEFAULT_SEARCH_LIMIT")


class TestSearch:
    """搜索边界情况测试"""

    def test_search_batch_mixed_modes(self):
        """批量搜索混合模式"""
        from agent_memory_lite.core.engine import MemoryEngine

        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "test.db")
            engine = MemoryEngine(db)

            engine.store("用户喜欢 Python", category="user_pref")
            engine.store("用户喜欢飞书", category="user_pref")

            queries = [
                {"query": "Python", "mode": "keyword", "limit": 3},
                {"query": "飞书", "mode": "keyword", "limit": 3},
            ]
            results = engine.search_batch(queries)
            assert len(results) == 2
            assert any("Python" in r["content"] for r in results[0])

            engine.close()
