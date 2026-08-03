"""测试用的假 Embedder（无 ONNX 依赖，确定性向量）"""


class FakeEmbedder:
    """模拟嵌入模型：固定维度，基于文本哈希的确定性假向量

    用于让语义/混合搜索与 migrate 测试在无模型环境下也可执行，
    避免向量路径测试被 pytest.skip 跳过。
    """

    dim = 384

    def embed(self, text: str) -> list[float]:
        # 确定性：相同文本返回相同向量，便于去重/一致性断言
        seed = abs(hash(text))
        return [(seed % 997) / 997.0] * self.dim

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
