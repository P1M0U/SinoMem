"""Agent Memory Lite — 轻量级中文友好的 Agent 记忆增强系统"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("agent-memory-lite")
except PackageNotFoundError:
    # 安装前运行（开发模式下 uv run）
    __version__ = "0.0.0.dev0"
