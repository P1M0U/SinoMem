"""SinoMem 插件层 — 多 Agent 自动记忆同步

提供统一的 BasePlugin 基类和针对各 Agent 的插件实现：

- base.BasePlugin         — 基类（直接用于简单场景）
- claude_code             — Claude Code 钩子脚本
- langchain               — LangChain BaseMemory 组件
- crewai                  — CrewAI Memory 组件
- autogen                 — AutoGen memory_provider 组件

快速开始：
    from sinomem.plugins import create_plugin

    plugin = create_plugin()
    plugin.auto_store("用户喜欢 Python")
    results = plugin.auto_search("编程语言")
"""

from .base import BasePlugin, create_plugin

__all__ = ["BasePlugin", "create_plugin"]
