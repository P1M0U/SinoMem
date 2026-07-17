"""嵌入模型封装 — onnxruntime + ONNX 量化模型

支持的模型：
- paraphrase-multilingual-MiniLM-L12-v2 (384维, 50+语言, 均值池化)
- bge-small-zh-v1.5 (512维, 中文优化, CLS池化)

自动检测模型类型，无需手动配置。
"""

import os
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from .config import DEFAULT_MODEL_DIR

# 默认模型仓库（Xenova 预转换 ONNX 格式）
_DEFAULT_REPO = "Xenova/bge-small-zh-v1.5"
_DEFAULT_FILES = ["onnx/model_quantized.onnx", "tokenizer.json"]


def ensure_model(
    model_dir: str | Path | None = None,
    repo: str = _DEFAULT_REPO,
    files: list[str] | None = None,
) -> bool:
    """确保 ONNX 模型已下载，缺少时尝试自动下载

    Args:
        model_dir: 模型存储目录
        repo: HuggingFace 仓库名
        files: 需要下载的文件列表

    Returns:
        True 表示模型已就绪，False 表示模型不可用
    """
    import logging

    _log = logging.getLogger(__name__)

    target_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
    onnx_dir = target_dir / "onnx"
    tokenizer_path = target_dir / "tokenizer.json"
    candidates = [
        onnx_dir / "model_quint8_avx2.onnx",
        onnx_dir / "model_quantized.onnx",
        onnx_dir / "model.onnx",
    ]

    # 模型已存在，无需下载
    if any(c.exists() for c in candidates) and tokenizer_path.exists():
        return True

    if files is None:
        files = _DEFAULT_FILES

    # 检查 huggingface_hub 是否可用
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        _log.warning(
            "自动下载模型需要 huggingface_hub，请先安装: pip install huggingface_hub"
        )
        return False

    # 检查镜像配置
    endpoint = None
    if "HF_ENDPOINT" in os.environ:
        endpoint = os.environ["HF_ENDPOINT"]
        _log.info("使用 HF 镜像: %s", endpoint)

    _log.info("正在自动下载嵌入模型 %s → %s ...", repo, target_dir)
    success = True
    for filename in files:
        try:
            hf_hub_download(
                repo_id=repo,
                filename=filename,
                local_dir=str(target_dir),
                endpoint=endpoint,
            )
            _log.info("  ✓ %s", filename)
        except Exception as e:
            _log.error("  ✗ %s 下载失败: %s", filename, e)
            success = False

    return success


def _count_session_inputs(session: ort.InferenceSession) -> int:
    """返回 ONNX 模型输入张量数量"""
    return len(session.get_inputs())


def _detect_model_type(session: ort.InferenceSession) -> str:
    """根据 ONNX 模型输出维度自动检测模型类型

    检测规则：
    - 512 维 → "bge"（BGE-small 系列）
    - 384 维 → "minilm"（MiniLM 系列）
    - 其他 → "minilm"（兜底）

    注意：不按输入数量判断，因为 Xenova 转出来的 BGE 也有 3 个输入。
    """
    output_dim = session.get_outputs()[0].shape[-1]
    output_dim = output_dim if isinstance(output_dim, int) else 0

    if output_dim == 512:
        return "bge"
    return "minilm"


class Embedder:
    """ONNX 嵌入模型封装"""

    def __init__(self, model_dir: str | Path | None = None):
        self.model_dir = Path(model_dir) if model_dir else DEFAULT_MODEL_DIR
        self._session: ort.InferenceSession | None = None
        self._tokenizer: Tokenizer | None = None
        self._dim: int = 0
        self._model_type: str = "minilm"  # "bge" | "minilm"

    @property
    def dim(self) -> int:
        """向量维度"""
        if self._dim == 0:
            self._load()
        return self._dim

    @property
    def model_type(self) -> str:
        """模型类型标识"""
        if self._session is None:
            self._load()
        return self._model_type

    def _load(self):
        """加载模型和分词器。

        MiniLM 优先加载量化版 model_quint8_avx2.onnx（~113MB），
        BGE 优先加载 model_quantized.onnx（~24MB），
        都不存在则回退到 model.onnx（fp32，较大）。
        """
        import logging

        _log = logging.getLogger(__name__)

        onnx_path = self.model_dir / "onnx"

        # 按优先级依次尝试
        candidates = [
            onnx_path / "model_quint8_avx2.onnx",  # MiniLM 量化版 ~113MB
            onnx_path
            / "model_quantized.onnx",  # BGE 量化版 ~24MB / 通用量化版
            onnx_path / "model.onnx",  # fp32 兜底
        ]
        model_file = None
        for candidate in candidates:
            if candidate.exists():
                model_file = candidate
                break

        if model_file is None:
            raise FileNotFoundError(
                f"ONNX 模型未找到: {onnx_path}\n"
                f"请运行以下命令下载模型到 {onnx_path}/ 目录:\n"
                "  pip install huggingface_hub\n"
                '  python -c "from huggingface_hub import hf_hub_download; '
                f"hf_hub_download('Xenova/bge-small-zh-v1.5', 'onnx/model_quantized.onnx', local_dir='{self.model_dir}'); "
                f"hf_hub_download('Xenova/bge-small-zh-v1.5', 'tokenizer.json', local_dir='{self.model_dir}')\"\n"
                "国内用户下载前请先设置: export HF_ENDPOINT=https://hf-mirror.com"
            )

        _log.info(
            "正在加载嵌入模型 %s（首次加载可能耗时数秒）...",
            model_file.name,
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

        # 自动检测模型类型
        self._model_type = _detect_model_type(self._session)
        self._dim = self._session.get_outputs()[0].shape[-1]
        if not isinstance(self._dim, int):
            self._dim = 384  # 兜底

        # 缓存输入数量（session 创建后不会改变）
        self._num_inputs = _count_session_inputs(self._session)

        _log.info(
            "嵌入模型加载完成 dim=%d type=%s", self._dim, self._model_type
        )

    def _build_inputs(self, ids: list[int], mask: list[int]) -> dict:
        """根据 ONNX 模型实际输入签名构造推理输入 dict"""
        inputs = {
            "input_ids": np.array([ids], dtype=np.int64),
            "attention_mask": np.array([mask], dtype=np.int64),
        }
        if self._num_inputs == 3:
            inputs["token_type_ids"] = np.array(
                [[0] * len(ids)], dtype=np.int64
            )
        return inputs

    def _build_batch_inputs(
        self, batch_ids: list[list[int]], batch_mask: list[list[int]]
    ) -> dict:
        """构造 batch 推理输入 dict"""
        inputs = {
            "input_ids": np.array(batch_ids, dtype=np.int64),
            "attention_mask": np.array(batch_mask, dtype=np.int64),
        }
        if self._num_inputs == 3:
            inputs["token_type_ids"] = np.zeros(
                (len(batch_ids), len(batch_ids[0])), dtype=np.int64
            )
        return inputs

    def _pool(
        self,
        token_embeddings: np.ndarray,
        attention_mask: np.ndarray,
    ) -> np.ndarray:
        """池化 + L2 归一化

        - BGE 模型：取 [CLS] token（位置 0）
        - MiniLM 模型：均值池化
        """
        if self._model_type == "bge":
            # BGE 论文推荐：CLS token + L2 归一化
            pooled = token_embeddings[:, 0, :]
        else:
            # MiniLM / sentence-transformers：均值池化
            mask_expanded = np.expand_dims(attention_mask, axis=-1)
            mask_expanded = np.broadcast_to(
                mask_expanded, token_embeddings.shape
            )
            sum_embeddings = np.sum(token_embeddings * mask_expanded, axis=1)
            sum_mask = np.clip(
                mask_expanded.sum(axis=1), a_min=1e-9, a_max=None
            )
            pooled = sum_embeddings / sum_mask

        # L2 归一化（两个模型都做）
        norm = np.linalg.norm(pooled, axis=-1, keepdims=True)
        return pooled / np.clip(norm, a_min=1e-9, a_max=None)

    def embed(self, text: str) -> list[float]:
        """单条文本嵌入"""
        if self._session is None:
            self._load()

        encoded = self._tokenizer.encode(text)
        inputs = self._build_inputs(encoded.ids, encoded.attention_mask)
        outputs = self._session.run(None, inputs)

        normalized = self._pool(outputs[0], inputs["attention_mask"])
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

        # 填充到相同长度，构造 batch 输入
        batch_ids = []
        batch_mask = []

        for encoded in encodings:
            pad_len = max_len - len(encoded.ids)
            ids = encoded.ids + [0] * pad_len
            mask = encoded.attention_mask + [0] * pad_len
            batch_ids.append(ids)
            batch_mask.append(mask)

        inputs = self._build_batch_inputs(batch_ids, batch_mask)
        outputs = self._session.run(None, inputs)

        # 逐样本池化（batch 内长度不一致，mask 逐行不同）
        token_embeddings = outputs[0]  # (batch_size, max_len, dim)
        attention_mask = np.array(batch_mask, dtype=np.int64)
        normalized = self._pool(token_embeddings, attention_mask)

        return normalized.tolist()
