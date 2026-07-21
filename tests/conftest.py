"""测试公共 fixture — 所有测试文件自动继承"""

import pytest

from sinomem.core.engine import MemoryEngine


@pytest.fixture
def engine(tmp_path):
    """每个测试用例使用独立的临时数据库（无嵌入模型）"""
    db_path = tmp_path / "test.db"
    eng = MemoryEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def engine_with_vec(tmp_path):
    """带向量索引的引擎（用于语义/混合搜索测试）"""
    try:
        from sinomem.core.embedder import Embedder

        embedder = Embedder()
        # 主动触发模型加载（懒加载在 .dim 才真正执行）
        _ = embedder.dim
        db_path = tmp_path / "test_vec.db"
        eng = MemoryEngine(db_path, embedder=embedder)
        yield eng
        eng.close()
    except Exception:
        pytest.skip("嵌入模型不可用，跳过向量测试")
