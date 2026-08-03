"""测试公共 fixture — 所有测试文件自动继承"""

import pytest

from sinomem.core.engine import MemoryEngine
from tests.fakes import FakeEmbedder


@pytest.fixture
def engine(tmp_path):
    """每个测试用例使用独立的临时数据库（无嵌入模型）"""
    db_path = tmp_path / "test.db"
    eng = MemoryEngine(db_path)
    yield eng
    eng.close()


@pytest.fixture
def engine_with_vec(tmp_path):
    """带向量索引的引擎（FakeEmbedder，无 ONNX 依赖）"""
    db_path = tmp_path / "test_vec.db"
    eng = MemoryEngine(db_path, embedder=FakeEmbedder())
    yield eng
    eng.close()
