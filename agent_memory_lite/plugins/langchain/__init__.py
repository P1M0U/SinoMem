"""LangChain BaseMemory 组件 — 一行 import 实现自动记忆同步

LangChain 的 BaseMemory 接口定义了 load_memory_variables() 和 save_context()，
Agent 在每轮对话前后自动调用，实现完全无感的记忆管理。

使用方式：
    from agent_memory_lite.plugins.langchain import AMLMemory

    memory = AMLMemory()
    agent = create_react_agent(llm, tools, memory=memory)
    # 每次对话前后自动检索/存储记忆，Agent 完全无感
"""

import contextlib
from typing import Any

from ..base import BasePlugin


class AMLMemory(BasePlugin):
    """LangChain 兼容的自动记忆组件

    实现 LangChain 的 BaseMemory 接口，对接 LangChain Agent 的生命周期：
    - load_memory_variables(): 对话前自动检索相关记忆
    - save_context(): 对话后自动提取并存储新记忆
    """

    # 兼容的 LangChain memory key
    memory_key: str = "agent_memory_lite"

    def __init__(self, db_path=None, memory_key="agent_memory_lite"):
        super().__init__(db_path=db_path)
        self.memory_key = memory_key

    @property
    def memory_variables(self) -> list[str]:
        """返回此 memory 提供的变量名列表"""
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, str]:
        """对话前自动调用 — 检索相关记忆并注入

        Args:
            inputs: LangChain 传入的当前输入，通常含 "input" 键

        Returns:
            {memory_key: 格式化后的记忆文本}
        """
        current_input = inputs.get("input", "") or str(inputs)

        if not current_input or len(current_input) < 3:
            return {self.memory_key: ""}

        try:
            memories = self.auto_search(current_input, mode="hybrid", limit=5)
        except Exception:
            return {self.memory_key: ""}

        if not memories:
            return {self.memory_key: ""}

        lines = ["## 相关长期记忆"]
        for i, m in enumerate(memories, 1):
            category = m.get("category", "general")
            content = m.get("content", "")
            tags = m.get("tags", [])
            tag_str = f" [{', '.join(tags)}]" if tags else ""
            lines.append(f"{i}. [{category}]{tag_str} {content}")

        return {self.memory_key: "\n".join(lines)}

    def save_context(
        self, inputs: dict[str, Any], outputs: dict[str, Any]
    ) -> None:
        """对话后自动调用 — 提取并存储值得记忆的信息

        Args:
            inputs: 用户输入
            outputs: Agent 输出
        """
        output_text = outputs.get("output", "") or str(outputs)

        # 仅存储足够长的输出（避免琐碎信息）
        if not output_text or len(output_text) < 30:
            return

        # 截取前 800 字符
        snippet = output_text[:800]

        # 存储失败不影响 Agent 主流程
        with contextlib.suppress(Exception):
            self.auto_store(
                content=snippet,
                category="project",
                tags=["langchain-auto"],
                importance=0.5,
            )

    def clear(self) -> None:
        """清空所有记忆"""
        engine = self._get_engine()
        engine.delete_all()


class AMLLangChainChatMemory(AMLMemory):
    """LangChain 对话场景专用 — 按会话粒度管理记忆

    与 AMLMemory 的区别：
    - 自动标记 session_id，方便按会话清理
    - save_context 同时存储用户输入和 Agent 输出
    """

    def __init__(self, session_id=None, db_path=None):
        super().__init__(db_path=db_path)
        import uuid

        self.session_id = session_id or str(uuid.uuid4())[:8]

    def save_context(
        self, inputs: dict[str, Any], outputs: dict[str, Any]
    ) -> None:
        """存储对话上下文（用户输入 + Agent 输出）"""
        input_text = inputs.get("input", "") or str(inputs)
        output_text = outputs.get("output", "") or str(outputs)

        # 存储用户输入中的关键信息
        if input_text and len(input_text) > 10:
            with contextlib.suppress(Exception):
                self.auto_store(
                    content=input_text[:500],
                    category="general",
                    tags=["langchain-chat", f"session-{self.session_id}"],
                    importance=0.4,
                )

        # 存储 Agent 输出中的重要信息
        if output_text and len(output_text) > 30:
            with contextlib.suppress(Exception):
                self.auto_store(
                    content=output_text[:500],
                    category="project",
                    tags=["langchain-chat", f"session-{self.session_id}"],
                    importance=0.5,
                )
