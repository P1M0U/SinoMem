"""AutoGen memory_provider 组件 — 自动记忆同步

AutoGen 的 memory_provider 接口在每轮对话前后自动调用：
- update_memory(): 对话后提取并存储记忆
- query_memory(): 对话前检索相关记忆

使用方式：
    from agent_memory_lite.plugins.autogen import AMLAutoGenMemory

    memory = AMLAutoGenMemory()
    assistant = AssistantAgent(
        name="assistant",
        memory_provider=memory,  # ← 一行接入
    )
"""

import contextlib
from typing import Any

from ..base import BasePlugin


class AMLAutoGenMemory(BasePlugin):
    """AutoGen 兼容的自动记忆组件

    实现 AutoGen memory_provider 接口：
    - query_memory(): 检索相关记忆
    - update_memory(): 存储新记忆
    """

    def __init__(self, db_path=None):
        super().__init__(db_path=db_path)

    def query_memory(
        self,
        query: str,
        limit: int = 5,
    ) -> str:
        """对话前检索相关记忆，返回格式化文本

        Args:
            query: 当前对话内容
            limit: 返回条数

        Returns:
            格式化的记忆文本（可直接拼接到 system prompt）
        """
        if not query or len(query) < 3:
            return ""

        try:
            memories = self.auto_search(query, mode="hybrid", limit=limit)
        except Exception:
            return ""

        if not memories:
            return ""

        lines = ["\n## Recent memories that may be relevant:"]
        for i, m in enumerate(memories, 1):
            content = m.get("content", "")
            # 粗略截断（避免超长）
            if len(content) > 200:
                content = content[:200] + "..."
            lines.append(f"{i}. {content}")

        return "\n".join(lines)

    def update_memory(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """对话后存储新记忆

        Args:
            content: 要存储的内容
            metadata: 元数据（category/tags/importance）
        """
        if not content or len(content) < 10:
            return

        category = "general"
        tags = ["autogen-auto"]
        importance = 0.5

        if metadata:
            category = metadata.get("category", category)
            tags = metadata.get("tags", tags)
            importance = metadata.get("importance", importance)

        with contextlib.suppress(Exception):
            self.auto_store(
                content=content[:800],
                category=category,
                tags=tags,
                importance=importance,
            )

    def clear_memory(self) -> None:
        """清空记忆（依赖 MemoryEngine.delete_all()）"""
        engine = self._get_engine()
        engine.delete_all()
