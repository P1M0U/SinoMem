"""嵌入模型封装 — onnxruntime + ONNX 量化模型

支持的模型：
- paraphrase-multilingual-MiniLM-L12-v2 (384维, 50+语言, 均值池化)
- bge-small-zh-v1.5 (512维, 中文优化, CLS池化)

自动检测模型类型，无需手动配置。
"""

import os
import shutil
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer

from .config import DEFAULT_MODEL_DIR

# 默认模型仓库（Xenova 预转换 ONNX 格式）
_DEFAULT_REPO = "Xenova/bge-small-zh-v1.5"
_DEFAULT_FILES = ["onnx/model_quantized.onnx", "tokenizer.json"]

# 国内 HuggingFace 镜像（中文用户优先使用）
_MIRROR_HF = "https://hf-mirror.com"

# 快速探测超时（秒），避免在不可达端点上等待过久
_PROBE_TIMEOUT = 3


def _probe_endpoint(
    endpoint: str | None, timeout: int = _PROBE_TIMEOUT
) -> bool:
    """快速探测 HuggingFace 端点是否可达（HEAD 请求 + 短超时）

    Args:
        endpoint: 端点 URL（None 表示 huggingface.co）
        timeout: 超时秒数

    Returns:
        True 表示端点可达，False 表示不可达或超时
    """
    import logging

    _log = logging.getLogger(__name__)

    try:
        import requests
    except ImportError:
        # requests 不可用时跳过探测，直接尝试下载
        return True

    base = endpoint if endpoint else "https://huggingface.co"
    probe_url = f"{base}/api/status"
    try:
        resp = requests.head(probe_url, timeout=timeout)
        # 2xx/3xx 视为可达
        return resp.status_code < 400
    except Exception:
        label = endpoint or "huggingface.co"
        _log.info("端点不可达（%ds 超时）: %s", timeout, label)
        return False


def _find_tokenizer_json(target_dir: Path) -> Path | None:
    """在 target_dir 及其子目录中搜索 tokenizer.json

    处理 tokenizer.json 因历史下载被放在子目录中的情况
    （如 bge-small-zh-v1.5/tokenizer.json）。

    Args:
        target_dir: 模型存储目录

    Returns:
        tokenizer.json 的路径，未找到返回 None
    """
    # 优先检查直接路径
    direct = target_dir / "tokenizer.json"
    if direct.exists():
        return direct

    # 搜索一级子目录
    if target_dir.is_dir():
        for child in sorted(target_dir.iterdir()):
            if child.is_dir():
                candidate = child / "tokenizer.json"
                if candidate.exists():
                    return candidate

    return None


def _find_onnx_file(target_dir: Path) -> Path | None:
    """在 target_dir 及其子目录中搜索 ONNX 模型文件

    Args:
        target_dir: 模型存储目录

    Returns:
        ONNX 模型文件的路径，未找到返回 None
    """
    onnx_dir = target_dir / "onnx"
    candidates = [
        onnx_dir / "model_quint8_avx2.onnx",
        onnx_dir / "model_quantized.onnx",
        onnx_dir / "model.onnx",
    ]
    for c in candidates:
        if c.exists():
            return c

    # 也搜索子目录
    if target_dir.is_dir():
        for child in sorted(target_dir.iterdir()):
            if child.is_dir() and child != onnx_dir:
                for fn in [
                    "model_quint8_avx2.onnx",
                    "model_quantized.onnx",
                    "model.onnx",
                ]:
                    candidate = child / "onnx" / fn
                    if candidate.exists():
                        return candidate

    return None


def _consolidate_model_files(
    target_dir: Path, found_onnx: Path, found_tokenizer: Path
) -> bool:
    """将散落在子目录中的模型文件统一复制到 target_dir 预期位置

    场景：用户之前用不同 local_dir 下载了模型，导致文件分布在子目录中。

    Args:
        target_dir: 预期的模型根目录
        found_onnx: 已找到的 ONNX 文件路径
        found_tokenizer: 已找到的 tokenizer.json 路径

    Returns:
        True 表示合并完成
    """
    import logging

    _log = logging.getLogger(__name__)

    onnx_dir = target_dir / "onnx"
    onnx_dir.mkdir(parents=True, exist_ok=True)

    dest_onnx = onnx_dir / found_onnx.name
    dest_tokenizer = target_dir / "tokenizer.json"

    if not dest_onnx.exists() and found_onnx != dest_onnx:
        _log.info("复制 %s → %s", found_onnx, dest_onnx)
        shutil.copy2(found_onnx, dest_onnx)

    if not dest_tokenizer.exists():
        _log.info("复制 %s → %s", found_tokenizer, dest_tokenizer)
        shutil.copy2(found_tokenizer, dest_tokenizer)

    return True


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

    # ── 第一步：检查模型文件是否已存在（含子目录容错搜索）──
    onnx_file = _find_onnx_file(target_dir)
    tokenizer_file = _find_tokenizer_json(target_dir)

    if onnx_file is not None and tokenizer_file is not None:
        # 文件存在但散落在子目录中 → 自动合并到预期位置
        if (
            onnx_file.parent != target_dir / "onnx"
            or tokenizer_file.parent != target_dir
        ):
            _consolidate_model_files(target_dir, onnx_file, tokenizer_file)
        return True

    if files is None:
        files = _DEFAULT_FILES

    # ── 第二步：检查 huggingface_hub 是否可用 ──
    try:
        from huggingface_hub import hf_hub_download
    except ImportError:
        _log.warning(
            "自动下载模型需要 huggingface_hub，请先安装: "
            "pip install huggingface_hub"
        )
        return False

    # ── 第三步：构建端点列表（国内镜像优先）──
    endpoints: list[str | None] = []
    if "HF_ENDPOINT" in os.environ:
        endpoints.append(os.environ["HF_ENDPOINT"])
        _log.info("使用 HF 镜像: %s", endpoints[0])
    else:
        # 国内用户优先走 hf-mirror.com，不可达再回退 huggingface.co
        endpoints.append(_MIRROR_HF)
        endpoints.append(None)

    # ── 第四步：快速探测 + 下载 ──
    # 跳过不可达的端点（短超时探测，避免 hf_hub_download 长重试）
    reachable = []
    for ep in endpoints:
        label = ep or "huggingface.co"
        if _probe_endpoint(ep):
            reachable.append(ep)
            _log.info("✓ 端点可达: %s", label)
        else:
            _log.warning("✗ 端点不可达，跳过: %s", label)

    if not reachable:
        _log.error(
            "所有端点均不可达，无法下载模型。"
            "请设置环境变量后重试: export HF_ENDPOINT=https://hf-mirror.com"
        )
        return False

    # 下载时使用较短超时（避免单个端点卡死过久）
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "8")

    _log.info("正在自动下载嵌入模型 %s → %s ...", repo, target_dir)
    for filename in files:
        downloaded = False
        last_error = None
        for endpoint in reachable:
            label = endpoint or "huggingface.co"
            try:
                _log.info("  下载 %s（通过 %s）...", filename, label)
                hf_hub_download(
                    repo_id=repo,
                    filename=filename,
                    local_dir=str(target_dir),
                    endpoint=endpoint,
                )
                downloaded = True
                _log.info("  ✓ %s", filename)
                break
            except Exception as e:
                last_error = e
                _log.debug("  %s 从 %s 下载失败: %s", filename, label, e)
                continue
        if not downloaded:
            _log.error("  ✗ %s 下载失败: %s", filename, last_error)

    # 检查最终是否就绪
    onnx_ok = _find_onnx_file(target_dir) is not None
    tokenizer_ok = _find_tokenizer_json(target_dir) is not None
    return onnx_ok and tokenizer_ok


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

        使用 _find_onnx_file / _find_tokenizer_json 多路径搜索，
        支持历史下载散落在子目录中的场景。
        """
        import logging

        _log = logging.getLogger(__name__)

        # 多路径搜索 ONNX 模型文件
        model_file = _find_onnx_file(self.model_dir)
        if model_file is None:
            onnx_path = self.model_dir / "onnx"
            raise FileNotFoundError(
                f"ONNX 模型未找到，请下载到 {onnx_path}/ 目录。\n"
                "  pip install huggingface_hub\n"
                f"  python -c \"from agent_memory_lite.core.embedder import ensure_model; ensure_model('{self.model_dir}')\"\n"
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

        # 多路径搜索分词器
        tokenizer_path = _find_tokenizer_json(self.model_dir)
        if tokenizer_path is None:
            raise FileNotFoundError(
                f"tokenizer.json 未找到: {self.model_dir}\n"
                "请设置 HF_ENDPOINT 后重新下载: "
                "export HF_ENDPOINT=https://hf-mirror.com"
            )

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
