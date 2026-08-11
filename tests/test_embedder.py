"""embedder 模型类型检测测试（mock session，无 ONNX 依赖）"""


class DummyOutput:
    def __init__(self, dim: int):
        self.shape = [-1, dim]


class DummySession:
    """模拟 ort.InferenceSession，仅暴露 get_outputs"""

    def __init__(self, dim: int = 384):
        self._dim = dim

    def get_outputs(self):
        return [DummyOutput(self._dim)]


def test_detect_model_type_by_name():
    """模型文件名优先识别（bge → CLS 池化）"""
    from sinomem.core.embedder import _detect_model_type

    s = DummySession(384)
    assert _detect_model_type(s, "bge-small-zh.onnx") == "bge"
    assert _detect_model_type(s, "model_quantized.onnx") == "minilm"
    assert _detect_model_type(s, "model.onnx") == "minilm"


def test_detect_model_type_multilingual():
    """多语言模型名识别为 minilm（均值池化）"""
    from sinomem.core.embedder import _detect_model_type

    s = DummySession(384)
    assert _detect_model_type(s, "model_quantized.onnx") == "minilm"


def test_detect_model_type_dim_fallback():
    """维度兜底：512 → bge，其他 → minilm"""
    from sinomem.core.embedder import _detect_model_type

    assert _detect_model_type(DummySession(512), "model.onnx") == "bge"
    assert _detect_model_type(DummySession(768), "model.onnx") == "minilm"
