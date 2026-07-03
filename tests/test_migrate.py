"""测试 migrate 迁移逻辑"""

import pytest

from agent_memory_lite.core.engine import MemoryEngine
from agent_memory_lite.tools.migrate import migrate_memories


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
            from agent_memory_lite.core.embedder import Embedder

            embedder = Embedder()
            _ = embedder.dim
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

        # 验证向量确实被添加
        from agent_memory_lite.core.embedder import Embedder

        embedder = Embedder()
        eng2 = MemoryEngine(db_path, embedder=embedder)
        assert eng2.stats()["vectors"] >= 2
        eng2.close()

    def test_migrate_force_rebuild(self, tmp_path):
        """--force 模式清空并重建向量"""
        try:
            from agent_memory_lite.core.embedder import Embedder

            embedder = Embedder()
            _ = embedder.dim
        except Exception:
            pytest.skip("嵌入模型不可用，跳过")

        db_path = str(tmp_path / "force_rebuild.db")
        # 先不用 embedder 存储（模拟无模型时积累的记忆）
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.store("测试记忆二")
        eng.close()

        # 第一次迁移：生成向量
        result1 = migrate_memories(db_path=db_path)
        assert result1["migrated"] == 2

        # 验证已有向量
        eng2 = MemoryEngine(db_path, embedder=embedder)
        assert eng2.stats()["vectors"] == 2
        dim_before = eng2.get_vec_dim()
        eng2.close()

        # --force 强制重建
        result2 = migrate_memories(db_path=db_path, force=True)
        assert result2["migrated"] == 2  # 清空后全部重新生成
        assert dim_before is not None

    def test_migrate_skip_existing(self, tmp_path):
        """已有的向量会被跳过（非 force 模式）"""
        try:
            from agent_memory_lite.core.embedder import Embedder

            embedder = Embedder()
            _ = embedder.dim
        except Exception:
            pytest.skip("嵌入模型不可用，跳过")

        db_path = str(tmp_path / "skip_existing.db")
        # 先不用 embedder 存储
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.close()

        # 第一次迁移：生成向量
        result1 = migrate_memories(db_path=db_path)
        assert result1["migrated"] == 1

        # 第二次迁移：应该跳过已有的（无新记忆）
        result2 = migrate_memories(db_path=db_path)
        assert result2["migrated"] == 0
        assert result2["skipped"] == 1

    def test_get_vec_dim(self, tmp_path):
        """get_vec_dim 返回正确的向量表示维度"""
        try:
            from agent_memory_lite.core.embedder import Embedder

            embedder = Embedder()
            _ = embedder.dim
        except Exception:
            pytest.skip("嵌入模型不可用，跳过")

        db_path = str(tmp_path / "vec_dim.db")
        eng = MemoryEngine(db_path, embedder=embedder)
        eng.store("测试记忆")
        eng.close()

        # 迁移后应该能读到维度
        migrate_memories(db_path=db_path)

        eng2 = MemoryEngine(db_path, embedder=embedder)
        dim = eng2.get_vec_dim()
        assert dim is not None
        assert dim > 0
        eng2.close()
