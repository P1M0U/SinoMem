"""测试 migrate 迁移逻辑（使用 FakeEmbedder，无 ONNX 依赖）"""

import pytest

from sinomem.core.engine import MemoryEngine
from sinomem.tools.migrate import migrate_memories
from tests.fakes import FakeEmbedder


def _run_migrate(monkeypatch, db_path, embedder=None, **kwargs):
    """用指定 Embedder 运行 migrate_memories（默认 FakeEmbedder）"""
    real_embedder = embedder or FakeEmbedder()

    def fake_create_engine(path=None, model_dir=None, with_embedder=True):
        return MemoryEngine(path, embedder=real_embedder)

    monkeypatch.setattr(
        "sinomem.core.engine.create_engine", fake_create_engine
    )
    return migrate_memories(db_path=db_path, **kwargs)


class TestMigrate:
    def test_migrate_empty_db(self, tmp_path, monkeypatch):
        """无记忆时返回 migrated=0"""
        db_path = str(tmp_path / "empty.db")
        eng = MemoryEngine(db_path)
        eng.close()

        result = _run_migrate(monkeypatch, db_path)
        assert result["total"] == 0
        assert result["migrated"] == 0

    def test_migrate_generates_vectors(self, tmp_path, monkeypatch):
        """生成向量"""
        db_path = str(tmp_path / "migrate_vec.db")
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.store("测试记忆二")
        eng.close()

        result = _run_migrate(monkeypatch, db_path)
        assert result["total"] == 2
        assert result["migrated"] == 2
        assert result["skipped"] == 0

        # 验证向量确实被添加
        eng2 = MemoryEngine(db_path, embedder=FakeEmbedder())
        assert eng2.stats()["vectors"] >= 2
        eng2.close()

    def test_migrate_force_rebuild(self, tmp_path, monkeypatch):
        """--force 模式清空并重建向量"""
        db_path = str(tmp_path / "force_rebuild.db")
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.store("测试记忆二")
        eng.close()

        result1 = _run_migrate(monkeypatch, db_path)
        assert result1["migrated"] == 2

        # 验证已有向量
        eng2 = MemoryEngine(db_path, embedder=FakeEmbedder())
        assert eng2.stats()["vectors"] == 2
        dim_before = eng2.get_vec_dim()
        eng2.close()

        # --force 强制重建
        result2 = _run_migrate(monkeypatch, db_path, force=True)
        assert result2["migrated"] == 2  # 清空后全部重新生成
        assert dim_before is not None

    def test_migrate_skip_existing(self, tmp_path, monkeypatch):
        """已有的向量会被跳过（非 force 模式）"""
        db_path = str(tmp_path / "skip_existing.db")
        eng = MemoryEngine(db_path)
        eng.store("测试记忆一")
        eng.close()

        # 第一次迁移：生成向量
        result1 = _run_migrate(monkeypatch, db_path)
        assert result1["migrated"] == 1

        # 第二次迁移：应该跳过已有的（无新记忆）
        result2 = _run_migrate(monkeypatch, db_path)
        assert result2["migrated"] == 0
        assert result2["skipped"] == 1

    def test_get_vec_dim(self, tmp_path, monkeypatch):
        """get_vec_dim 返回正确的向量表示维度"""
        db_path = str(tmp_path / "vec_dim.db")
        eng = MemoryEngine(db_path, embedder=FakeEmbedder())
        eng.store("测试记忆")
        eng.close()

        # 迁移后应该能读到维度
        _run_migrate(monkeypatch, db_path)

        eng2 = MemoryEngine(db_path, embedder=FakeEmbedder())
        dim = eng2.get_vec_dim()
        assert dim is not None
        assert dim > 0
        eng2.close()

    def test_migrate_force_dim_change(self, tmp_path, monkeypatch):
        """--force 模型维度切换时重建向量表

        历史 bug：clear_vectors 只 DELETE 不重建表，
        新维度向量写入旧维度 vec0 表必然失败。
        """
        db_path = str(tmp_path / "dim_change.db")
        # 用无 embedder 引擎存储，记忆不带向量（模拟旧库无向量状态）
        eng = MemoryEngine(db_path)
        eng.store("记忆一")
        eng.close()

        # 第一次迁移（384 维）
        result1 = _run_migrate(monkeypatch, db_path)
        assert result1["migrated"] == 1
        assert (
            MemoryEngine(db_path, embedder=FakeEmbedder()).get_vec_dim() == 384
        )

        # 模拟切换到 768 维模型
        class FakeEmbedder768(FakeEmbedder):
            dim = 768

        # 无 --force 时应报维度不匹配错误
        with pytest.raises(RuntimeError):
            _run_migrate(monkeypatch, db_path, embedder=FakeEmbedder768())

        # --force 时应重建向量表为新维度
        result2 = _run_migrate(
            monkeypatch,
            db_path,
            embedder=FakeEmbedder768(),
            force=True,
        )
        assert result2["dim_changed"] is True
        assert result2["migrated"] >= 1
        assert (
            MemoryEngine(db_path, embedder=FakeEmbedder768()).get_vec_dim()
            == 768
        )
