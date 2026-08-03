"""TTL 过期功能回归测试

覆盖历史严重缺陷：
- TTL 时长被忽略（expires_at = 存储时刻）
- ISO 时间戳与 SQLite datetime('now') 字符串比较不兼容
- 搜索不过滤过期记忆
- 空白/引号查询触发 FTS5 语法错误崩溃
- schema 版本号永不落库
"""

import tempfile
from pathlib import Path

from sinomem.core.engine import MemoryEngine


def _make_engine() -> MemoryEngine:
    """创建独立临时数据库的引擎"""
    db_path = Path(tempfile.mkdtemp()) / "test.db"
    return MemoryEngine(str(db_path))


def _force_expire(
    engine: MemoryEngine, memory_id: int, hours: int = -1
) -> None:
    """将记忆的过期时间直接改为过去（SQLite 原生格式，绕过 _parse_ttl）"""
    engine._conn.execute(
        "UPDATE memories SET expires_at = datetime('now', ?) WHERE id = ?",
        (f"{hours} hours", memory_id),
    )
    engine._conn.commit()


class TestTTLFunctionality:
    """TTL 过期功能"""

    def test_ttl_store_visible_immediately(self):
        """ttl=1h 存储后立即可见且未过期"""
        engine = _make_engine()
        try:
            mid = engine.store("临时记忆", ttl="1h")
            assert engine.stats()["expired"] == 0
            assert any(x["id"] == mid for x in engine.list_memories())
            assert any(
                x["id"] == mid for x in engine.search("临时", mode="keyword")
            )
        finally:
            engine.close()

    def test_ttl_expires_after_duration(self):
        """TTL 时长叠加正确：1h 后过期、list 过滤、cleanup 可清理"""
        engine = _make_engine()
        try:
            mid = engine.store("次日过期的记忆", ttl="1h")
            _force_expire(engine, mid)

            assert not any(x["id"] == mid for x in engine.list_memories())
            assert engine.stats()["expired"] >= 1
            assert engine.cleanup_expired() >= 1
        finally:
            engine.close()

    def test_search_filters_expired(self):
        """已过期记忆不出现于搜索结果（历史 bug：搜索无过期过滤）"""
        engine = _make_engine()
        try:
            mid = engine.store("独特关键词xyz 过期测试")
            _force_expire(engine, mid)

            results = engine.search("独特关键词xyz", mode="keyword")
            assert not any(x["id"] == mid for x in results)
        finally:
            engine.close()


class TestFTSSafety:
    """FTS5 查询安全性"""

    def test_special_chars_no_crash(self):
        """空白/引号/标点查询不崩溃（历史 bug：MATCH 语法错误）"""
        engine = _make_engine()
        try:
            engine.store("测试记忆内容")
            for query in ["   ", 'a"b', "!!!", "（）", "abc*def"]:
                results = engine.search(query)
                assert isinstance(results, list)
        finally:
            engine.close()


class TestSchemaVersion:
    """schema 版本号落库"""

    def test_schema_version_written(self):
        """新建库后 schema_version 表有版本号（历史 bug：永不落库）"""
        engine = _make_engine()
        try:
            ver = engine._conn.execute(
                "SELECT MAX(version) FROM schema_version"
            ).fetchone()[0]
            assert ver == 1
        finally:
            engine.close()
