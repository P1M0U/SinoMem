"""Hermes MemoryProvider 适配器

提供两套 API：

1. Hermes 原生接口 — AgentMemoryLiteProvider（实现 MemoryProvider）
2. BasePlugin Python API — HermesPlugin（统一插件接口）

快速使用：
    # 方式 1: Hermes 原生（由 plugin.yaml 自动加载）
    from sinomem.plugins.hermes import AgentMemoryLiteProvider

    # 方式 2: BasePlugin Python API
    from sinomem.plugins.hermes import HermesPlugin
    plugin = HermesPlugin()
    plugin.auto_store("用户喜欢飞书")
"""

from ..base import BasePlugin
from .provider import AgentMemoryLiteProvider


class HermesPlugin(BasePlugin):
    """Hermes Agent 的 BasePlugin 风格封装

    提供与 Claude Code / LangChain 等插件一致的 auto_store/auto_search 接口。
    底层 engine 创建由 MemoryEngine 处理，与 AgentMemoryLiteProvider 共享数据库。
    """

    def __init__(self, db_path=None):
        super().__init__(db_path=db_path)


__all__ = ["AgentMemoryLiteProvider", "HermesPlugin"]
