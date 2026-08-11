"""测试用的假 Embedder（无 ONNX 依赖，确定性向量）"""

import math
import random
import re

# 匹配中文/英文/数字 token（简化分词，模拟共享关键词的语义相关）
_TOKEN_RE = re.compile(r"[\w一-鿿]+")


class FakeEmbedder:
    """模拟嵌入模型：Bag-of-Words + hashing trick 的确定性语义向量

    设计要点：
    - 相同文本 → 相同向量（保证去重/一致性断言）
    - 共享关键词的文本 → 向量更接近（使语义搜索测试具备真实区分度，
      而不是所有向量同方向导致距离恒为 0）
    - 无 ONNX 依赖，让语义/混合搜索与 migrate 测试在无模型环境可执行
    """

    dim = 384

    def _token_vector(self, token: str) -> list[float]:
        """单个 token 的确定性伪随机向量"""
        rng = random.Random(hash(token))
        return [rng.random() for _ in range(self.dim)]

    def embed(self, text: str) -> list[float]:
        # 简化分词：提取中英文/数字 token；无 token 时退回整串
        tokens = _TOKEN_RE.findall(text) or [text]

        # Bag-of-Words 累加各 token 向量后 L2 归一化
        v = [0.0] * self.dim
        for t in tokens:
            tv = self._token_vector(t)
            v = [a + b for a, b in zip(v, tv, strict=True)]
        norm = math.sqrt(sum(x * x for x in v))
        if norm == 0:
            return v
        return [x / norm for x in v]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]
