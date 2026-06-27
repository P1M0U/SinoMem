"""嵌入模型封装 — onnxruntime + ONNX 量化模型"""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from .config import DEFAULT_MODEL_DIR


class Embedder:
    """ONNX 嵌入模型封装"""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._session: ort.InferenceSession | None = None
        self._tokenizer: Tokenizer | None = None
        self._dim: int = 0

    @property
    def dim(self) -> int:
        """向量维度"""
        if self._dim == 0:
            self._load()
        return self._dim

    def _load(self):
        """加载模型和分词器"""
        # 加载 ONNX 模型（优先量化版）
        onnx_path = self.model_dir / "onnx"
        model_file = onnx_path / "model_quantized.onnx"
        if not model_file.exists():
            model_file = onnx_path / "model.onnx"
        if not model_file.exists():
            raise FileNotFoundError(
                f"ONNX 模型未找到: {onnx_path}\n请下载模型到 {onnx_path}/ 目录"
            )

        self._session = ort.InferenceSession(
            str(model_file),
            providers=["CPUExecutionProvider"],
        )

        # 加载分词器
        tokenizer_path = self.model_dir / "tokenizer.json"
        if not tokenizer_path.exists():
            raise FileNotFoundError(f"tokenizer.json 未找到: {tokenizer_path}")

        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))

        # 获取输出维度
        output_shape = self._session.get_outputs()[0].shape
        self._dim = (
            output_shape[-1] if isinstance(output_shape[-1], int) else 384
        )

    def embed(self, text: str) -> list[float]:
        """单条文本嵌入"""
        if self._session is None:
            self._load()

        # 分词
        encoded = self._tokenizer.encode(text)

        # 准备输入
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        token_type_ids = np.array(
            [getattr(encoded, "type_ids", [0] * len(encoded.ids))],
            dtype=np.int64,
        )

        # 推理
        outputs = self._session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # 平均池化 + 归一化
        token_embeddings = outputs[0]  # (1, seq_len, dim)
        mask_expanded = np.expand_dims(encoded.attention_mask, axis=-1)
        mask_expanded = np.broadcast_to(mask_expanded, token_embeddings.shape)

        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        pooled = sum_embeddings / sum_mask

        # L2 归一化
        norm = np.linalg.norm(pooled, axis=1, keepdims=True)
        normalized = pooled / np.clip(norm, a_min=1e-9, a_max=None)

        return normalized[0].tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量文本嵌入 — 利用 ONNX Runtime batch 推理"""
        if not texts:
            return []
        if len(texts) == 1:
            return [self.embed(texts[0])]

        if self._session is None:
            self._load()

        # 批量分词
        encodings = [self._tokenizer.encode(text) for text in texts]
        max_len = max(len(e.ids) for e in encodings)

        # 填充到相同长度，构造 batch 输入 (batch_size, max_len)
        batch_ids = []
        batch_mask = []
        batch_type_ids = []

        for encoded in encodings:
            pad_len = max_len - len(encoded.ids)
            ids = encoded.ids + [0] * pad_len
            mask = encoded.attention_mask + [0] * pad_len
            type_ids = (
                getattr(encoded, "type_ids", [0] * len(encoded.ids))
                + [0] * pad_len
            )

            batch_ids.append(ids)
            batch_mask.append(mask)
            batch_type_ids.append(type_ids)

        input_ids = np.array(batch_ids, dtype=np.int64)
        attention_mask = np.array(batch_mask, dtype=np.int64)
        token_type_ids = np.array(batch_type_ids, dtype=np.int64)

        # 单次 batch 推理
        outputs = self._session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )

        # 平均池化 + L2 归一化（逐样本）
        token_embeddings = outputs[0]  # (batch_size, max_len, dim)
        mask_expanded = np.expand_dims(attention_mask, axis=-1)
        mask_expanded = np.broadcast_to(mask_expanded, token_embeddings.shape)

        sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
        sum_mask = np.clip(mask_expanded.sum(axis=1), a_min=1e-9, a_max=None)
        pooled = sum_embeddings / sum_mask

        # L2 归一化
        norms = np.linalg.norm(pooled, axis=1, keepdims=True)
        normalized = pooled / np.clip(norms, a_min=1e-9, a_max=None)

        return normalized.tolist()
