"""测试 migrate 迁移逻辑"""

import pytest

from agent_memory_lite.engine import MemoryEngine
from agent_memory_lite.migrate import migrate_memories


@pytest.fixture
def engine(tmp_path):
    db_path = tmp_path / "test_migrate.db"
    eng = MemoryEngine(db_path)
    yield eng
    eng.close()


class TestMigrate:
    def test_migrate_empty_db(self, tmp_path):
        """无记忆时返回 migrated=0"""
        db_path = str(tmp_path / "empty.db")
        # 先创建数据库文件
        eng = MemoryEngine(db_path)
        eng.close()

        try:
            result = migrate_memories(db_path=db_path)
        except RuntimeError as e:
            if "嵌入模型不可用" in str(e):
                pytest.skip("嵌入模型不可用，跳过")
            raise
        assert result["total"] == 0
        assert result["migrated"] == 0

    def test_migrate_generates_vectors(self, tmp_path):
        """有嵌入模型时生成向量"""
        try:
            from agent_memory_lite.embedder import Embedder

            Embedder()
        except Exception:
            pytest.skip("嵌入模型不可用，跳过")

        db_path = str(tmp_path / "migrate_vec.db")
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.store("测试记忆二")
        eng.close()

        result = migrate_memories(db_path=db_path)
        assert result["total"] == 2
        assert result["migrated"] == 2
        assert result["skipped"] == 0

        # 验证向量确实被添加（需要 embedder 才能识别向量表）
        from agent_memory_lite.embedder import Embedder

        embedder = Embedder()
        eng2 = MemoryEngine(db_path, embedder=embedder)
        assert eng2.stats()["vectors"] >= 2
        eng2.close()
