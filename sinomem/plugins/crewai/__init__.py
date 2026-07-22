"""CrewAI Memory 组件 — 一行 import 实现自动记忆同步

⚠️ 状态: WIP — 尚未对接 CrewAI 的 Memory 接口生命周期钩子。
当前实现基于 BasePlugin 基类，用户需手动调用 search/save。
欢迎贡献完整的 CrewAI Memory 集成方案。

CrewAI 的 Memory 接口通过 crew.memory 属性注入，自动在每轮对话前后
检索/存储记忆。

使用方式：
    from sinomem.plugins.crewai import SinoCrewMemory

    crew = Crew(
        agents=[...],
        tasks=[...],
        memory=SinoCrewMemory(),  # ← 一行接入
    )
    crew.kickoff()
"""

import contextlib
from typing import Any

from ..base import BasePlugin


class SinoCrewMemory(BasePlugin):
    """CrewAI 兼容的自动记忆组件

    实现 CrewAI Memory 接口的核心方法：
    - search(): 检索相关记忆（对话前自动调用）
    - save(): 存储新记忆（对话后自动调用）
    """

    def __init__(self, db_path=None):
        super().__init__(db_path=db_path)
        self._session_context = ""

    def search(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> list[dict]:
        """检索与当前任务相关的长期记忆

        CrewAI 在每个 task 执行前调用此方法，将结果注入到 Agent 的上下文中。

        Args:
            query: 搜索查询（通常是 task 描述）
            limit: 返回条数
            score_threshold: 最低相关性阈值（暂未实现，保留接口兼容）

        Returns:
            相关记忆列表（dict 包含 content/category/tags/score）
        """
        if not query or len(query) < 3:
            return []

        try:
            return self.auto_search(query, mode="hybrid", limit=limit)
        except Exception:
            return []

    def save(
        self,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """存储记忆

        CrewAI 在 task 执行后调用此方法保存有价值的信息。

        Args:
            content: 记忆内容
            metadata: 元数据（category/tags/importance）
        """
        category = "general"
        tags = ["crewai-auto"]
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

    def reset(self) -> None:
        """重置会话上下文"""
        self._session_context = ""


# 向后兼容别名（v0.7.x 旧名，后续版本将移除）
AMLCrewMemory = SinoCrewMemory
