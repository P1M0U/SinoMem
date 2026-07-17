"""Agent Memory Lite — 轻量级中文友好的 Agent 记忆增强系统

使用方式:
    from agent_memory_lite import create_engine

    engine = create_engine()
    engine.store("用户喜欢 Python", category="user_pref")
    results = engine.search("Python", mode="hybrid")
"""

from importlib.metadata import PackageNotFoundError, version

from .core.engine import MemoryEngine, create_engine
from .plugins.base import BasePlugin, create_plugin

try:
    __version__ = version("agent-memory-lite")
except PackageNotFoundError:
    # 安装前运行（开发模式下 uv run）
    __version__ = "0.0.0.dev0"

__all__ = [
    "__version__",
    "MemoryEngine",
    "create_engine",
    "BasePlugin",
    "create_plugin",
]
