"""插件基类 — 定义统一的自动记忆同步接口

所有插件（Hermes / Claude Code / LangChain / CrewAI / AutoGen）
都继承此基类，提供统一的：
- auto_store: 自动存储记忆（被动触发）
- auto_search: 自动检索相关记忆
- inject_context: 将记忆上下文注入到 prompt
"""

from pathlib import Path
from typing import Any

from ..core.config import DEFAULT_DB_PATH


class BasePlugin:
    """自动记忆同步插件的抽象基类

    子类只需关注两件事：
    1. 何时触发存储（钩子 / 回调 / 接口方法）
    2. 何时注入上下文（在 LLM 调用前）

    实际的存储/检索逻辑由 MemoryEngine 处理，插件只负责对接。
    """

    def __init__(
        self,
        engine=None,
        db_path: str | Path | None = None,
    ):
        self._engine = engine
        self._db_path = Path(db_path) if db_path else DEFAULT_DB_PATH

    # ── 引擎懒加载 ──

    def _get_engine(self):
        """懒加载 MemoryEngine（首次使用时创建）"""
        if self._engine is None:
            from ..core.engine import create_engine

            self._engine = create_engine(str(self._db_path))
        return self._engine

    # ── 核心 API ──

    def auto_store(
        self,
        content: str,
        category: str = "general",
        tags: list[str] | None = None,
        importance: float = 0.5,
        ttl: str | None = None,
    ) -> int:
        """自动存储记忆（被动触发，Agent 无感）

        Args:
            content: 记忆内容
            category: 分类（user_pref / project / tool / general）
            tags: 标签列表
            importance: 重要性 0.0~1.0
            ttl: 过期时间（"30d" / "24h" 等）

        Returns:
            记忆 id，重复内容则返回已有 id
        """
        if tags is None:
            tags = []
        engine = self._get_engine()
        return engine.store(
            content=content,
            category=category,
            tags=tags,
            skip_duplicate=True,
            ttl=ttl,
            importance=importance,
        )

    def auto_search(
        self,
        query: str,
        mode: str = "hybrid",
        limit: int = 5,
    ) -> list[dict]:
        """自动检索相关记忆

        Args:
            query: 搜索关键词（通常取用户当前 prompt）
            mode: keyword / semantic / hybrid
            limit: 返回条数

        Returns:
            相关记忆列表
        """
        engine = self._get_engine()
        return engine.search(query=query, mode=mode, limit=limit)

    def inject_context(
        self,
        current_prompt: str,
        mode: str = "hybrid",
        limit: int = 3,
        prefix: str = "\n\n## 相关记忆\n",
        format_memory=None,
    ) -> str:
        # 注: format_memory 类型为 Optional[Callable]，此处避免类体求值
        """将相关记忆上下文注入到用户 prompt 中

        Args:
            current_prompt: 用户的当前输入
            mode: 搜索模式
            limit: 最多注入几条记忆
            prefix: 注入块的前缀标题
            format_memory: 自定义格式化函数 (dict) -> str

        Returns:
            注入后的增强 prompt（原 prompt + 相关记忆）
        """
        memories = self.auto_search(current_prompt, mode=mode, limit=limit)

        if not memories:
            return current_prompt

        if format_memory is None:
            format_memory = self._default_format

        lines = [prefix]
        for i, m in enumerate(memories, 1):
            lines.append(
                format_memory(m, index=i, is_last=(i == len(memories)))
            )

        return current_prompt + "\n".join(lines)

    @staticmethod
    def _default_format(
        memory: dict, index: int = 0, is_last: bool = True
    ) -> str:
        """默认记忆格式化

        Args:
            memory: 记忆字典
            index: 序号
            is_last: 是否是最后一条
        """
        category = memory.get("category", "general")
        content = memory.get("content", "")
        tags = memory.get("tags", [])

        tag_str = f" [{', '.join(tags)}]" if tags else ""
        separator = "\n" if not is_last else ""

        return f"{index}. [{category}]{tag_str} {content}{separator}"

    # ── 生命周期 ──

    def close(self):
        """关闭插件（释放引擎资源）"""
        if self._engine:
            self._engine.close()
            self._engine = None

    def __repr__(self):
        return f"{self.__class__.__name__}(db={self._db_path})"

    # ── 子类可覆写 ──

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """子类覆写：Agent 写入记忆时的回调

        由子类根据各 Agent 的钩子机制调用此方法。
        """
        category = "general"
        tags = []

        if metadata:
            if "category" in metadata:
                category = metadata["category"]
            if "tags" in metadata:
                tags = metadata["tags"]

        self.auto_store(content=content, category=category, tags=tags)


def create_plugin(
    db_path: str | Path | None = None,
) -> "BasePlugin":
    """工厂函数：快速创建 BasePlugin 实例

    用于简单场景 —— 不需要子类化，直接使用基类的基本功能。
    对于需要深度定制的场景（LangChain/CrewAI 等），请使用对应的子类。

    Args:
        db_path: 数据库路径

    Returns:
        BasePlugin 实例

    Usage:
        from agent_memory_lite.plugins import create_plugin

        plugin = create_plugin()
        plugin.auto_store("用户喜欢 Python")
        results = plugin.auto_search("编程语言")
    """
    return BasePlugin(db_path=db_path)
