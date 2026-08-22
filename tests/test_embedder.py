"""embedder 池化逻辑测试（mock ndarray，无 ONNX 依赖）

固定使用 bge 模型（CLS 池化 + L2 归一化）。
"""

import numpy as np

from sinomem.core.embedder import Embedder


def _make_poolable() -> np.ndarray:
    """构造 2 样本 × 3 token × 4 维的 token 嵌入，确保 CLS 行非零"""
    return np.array(
        [
            [[1.0, 0.0, 0.0, 0.0], [0.0, 2.0, 0.0, 0.0], [0.0, 0.0, 3.0, 0.0]],
            [[0.0, 0.0, 0.0, 4.0], [1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0]],
        ],
        dtype=np.float64,
    )


def _pool(embeddings: np.ndarray) -> np.ndarray:
    """调用 Embedder._pool（无状态方法，self 仅用于占位）"""
    return Embedder._pool(None, embeddings)


def test_pool_uses_cls_token():
    """CLS 池化取位置 0 的 token 嵌入（bge 论文推荐）"""
    emb = _make_poolable()
    pooled = _pool(emb)
    assert pooled.shape == (2, 4)
    # CLS 行 = 位置 0 的 token 向量（L2 归一化前后方向一致）
    np.testing.assert_allclose(
        pooled[0], emb[0, 0, :] / np.linalg.norm(emb[0, 0, :])
    )


def test_pool_l2_normalized():
    """池化输出为 L2 归一化向量（模长 = 1）"""
    pooled = _pool(_make_poolable())
    norms = np.linalg.norm(pooled, axis=-1)
    np.testing.assert_allclose(norms, np.ones(2), atol=1e-6)


def test_pool_zero_cls_does_not_crash():
    """CLS 行全零时除以 clip 下限不崩溃（防御性兜底）"""
    emb = np.zeros((1, 3, 4), dtype=np.float64)
    pooled = _pool(emb)
    assert pooled.shape == (1, 4)
    assert np.all(np.isfinite(pooled))
