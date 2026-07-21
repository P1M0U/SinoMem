"""Hermes MemoryProvider 适配器 — 核心实现

功能：
- 包装 SinoMem（sinomem）的 MemoryEngine
- 提供 memory_search / memory_store / memory_list 工具
- 自动同步内置 memory 工具写入到 sinomem 数据库
- 支持 jieba 中文分词 + FTS5 搜索 + ONNX 语义搜索
"""

import contextvars
import importlib
import importlib.util  # 显式导入子模块
import logging
import os
from pathlib import Path
from typing import Any

# 防递归写入标记（ContextVar 替代 threading.current_thread() 属性）
_writing_flag: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "_sinomem_writing", default=False
)

# Hermes 运行时依赖（仅在 Hermes 环境中可用）
from agent.memory_provider import MemoryProvider  # noqa: E402
from tools.registry import tool_error  # noqa: E402

from ...core.engine import create_engine as _create_engine  # noqa: E402

# ── 路径配置 ──

_AGENT_MEMORY_DB = Path.home() / ".sinomem" / "memory.db"

# 后向兼容：保留 SINOMEM_HOME 环境变量，用于自定义数据库路径
if os.environ.get("SINOMEM_HOME"):
    _db_override = Path(os.environ["SINOMEM_HOME"]) / "memory.db"
    if _db_override.parent.exists():
        _AGENT_MEMORY_DB = _db_override


# ── Provider 实现 ──


class SinoMemProvider(MemoryProvider):
    """Hermes Memory Provider 适配器 — 包装 SinoMem（sinomem）"""

    name = "sinomem"

    def __init__(self):
        self._engine = None
        self._session_id = None
        self._hermes_home = None
        self._agent_context = None
        self._skip_writes = False  # cron/subagent 不镜像写入
        self._logger = logging.getLogger("hermes.memory.sinomem")

    def is_available(self) -> bool:
        """检查 sinomem 是否可用"""
        try:
            if importlib.util.find_spec("sinomem") is None:
                self._logger.warning("sinomem 未安装")
                return False
            return True
        except Exception as e:
            self._logger.warning(f"is_available 检查异常: {e}")
            return False

    def get_config_schema(self) -> list[dict]:
        """返回 provider 配置项说明，供 hermes memory status 展示"""
        return [
            {
                "key": "db_path",
                "type": "path",
                "description": "SQLite 数据库路径",
                "default": str(_AGENT_MEMORY_DB),
            },
        ]

    def initialize(self, session_id: str, **kwargs) -> None:
        """初始化 provider"""
        self._session_id = session_id
        self._hermes_home = kwargs.get(
            "hermes_home", str(Path.home() / ".hermes")
        )
        self._agent_context = kwargs.get("agent_context", "primary")

        # 非主上下文（cron/subagent）不镜像写入
        if self._agent_context != "primary":
            self._skip_writes = True

        # 支持通过环境变量或 kwargs 覆盖数据库路径
        db_path = kwargs.get("db_path") or str(_AGENT_MEMORY_DB)

        try:
            self._engine = _create_engine(db_path)
            self._logger.info(
                f"SinoMem 初始化成功 (session={session_id}, "
                f"context={self._agent_context}, skip_writes={self._skip_writes})"
            )
        except Exception as e:
            self._logger.error(f"初始化失败: {e}")
            raise

    def get_tool_schemas(self) -> list[dict[str, Any]]:
        """返回工具 schema"""
        return [
            {
                "name": "memory_search",
                "description": (
                    "搜索长期记忆（中文友好，jieba 分词）。支持三种搜索模式：\n"
                    "• keyword — jieba 中文分词 + FTS5 关键词匹配\n"
                    "• semantic — ONNX 本地语义向量搜索（需嵌入模型）\n"
                    "• hybrid — 关键词 + 语义加权混合排序（推荐）"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或问题",
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["keyword", "semantic", "hybrid"],
                            "description": "搜索模式",
                            "default": "hybrid",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回条数",
                            "default": 5,
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "memory_store",
                "description": (
                    "存储一条长期记忆。自动去重，自动 jieba 中文分词建索引。"
                    "当用户明确要求记住某事，或你发现值得跨会话保留的信息时使用。"
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "记忆内容",
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "user_pref",
                                "project",
                                "tool",
                                "general",
                            ],
                            "description": "分类",
                            "default": "general",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表",
                        },
                        "ttl": {
                            "type": "string",
                            "description": (
                                "过期时间，如 30d / 24h / 7d12h"
                                "（不填永不过期）"
                            ),
                        },
                        "importance": {
                            "type": "number",
                            "description": "重要性评分 0.0~1.0（默认 0.5）",
                            "default": 0.5,
                        },
                    },
                    "required": ["content"],
                },
            },
            {
                "name": "memory_list",
                "description": "列出已存储的记忆，可按分类过滤。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": [
                                "user_pref",
                                "project",
                                "tool",
                                "general",
                            ],
                            "description": "按分类过滤（不填返回全部）",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回条数",
                            "default": 20,
                        },
                    },
                },
            },
        ]

    def handle_tool_call(self, tool_name: str, arguments: dict) -> str:
        """处理工具调用"""
        import json

        try:
            if tool_name == "memory_search":
                results = self._engine.search(
                    arguments["query"],
                    mode=arguments.get("mode", "hybrid"),
                    limit=arguments.get("limit", 5),
                )
                return json.dumps(results, ensure_ascii=False, default=str)

            elif tool_name == "memory_store":
                result = self._engine.store(
                    content=arguments["content"],
                    category=arguments.get("category", "general"),
                    tags=arguments.get("tags"),
                    ttl=arguments.get("ttl"),
                    importance=arguments.get("importance", 0.5),
                )
                return json.dumps(result, ensure_ascii=False, default=str)

            elif tool_name == "memory_list":
                results = self._engine.list_memories(
                    category=arguments.get("category"),
                    limit=arguments.get("limit", 20),
                )
                return json.dumps(results, ensure_ascii=False, default=str)

            else:
                return tool_error(f"未知工具: {tool_name}")

        except Exception as e:
            self._logger.error(f"工具调用失败 [{tool_name}]: {e}")
            return tool_error(str(e))

    def system_prompt_block(self) -> str:
        """返回系统提示块"""
        if self._engine is None:
            return "# SinoMem\nInitializing..."
        try:
            stats = self._engine.stats()
            total = stats.get("total", 0)
            return (
                "# SinoMem\n"
                f"Active. {total} memories stored with jieba Chinese tokenization "
                "and optional semantic search.\n"
                "Use memory_search to recall context (supports keyword/semantic/hybrid modes).\n"
                "Use memory_store to persist new information."
            )
        except Exception:
            return "# SinoMem\nActive (stats unavailable)."

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        """
        内置 memory 工具写入时的钩子 — 镜像到 sinomem

        ⚠️ 这是自动同步的核心机制！
        """
        # 跳过非主上下文
        if self._skip_writes:
            return

        # 避免递归：ContextVar 保证线程/协程安全
        if _writing_flag.get():
            return

        try:
            _writing_flag.set(True)
            self._logger.debug(f"on_memory_write: {action} {target}")

            if action in ("add", "replace") and content:
                category = "general"
                tags = []

                if metadata:
                    if "category" in metadata:
                        category = metadata["category"]
                    if "tags" in metadata:
                        tags = metadata["tags"]

                self._engine.store(
                    content=content,
                    category=category,
                    tags=tags if tags else ["hermes-sync"],
                )
                self._logger.debug(f"同步成功: {content[:50]}...")

        except Exception as e:
            self._logger.warning(f"on_memory_write 同步失败: {e}")
        finally:
            _writing_flag.set(False)

    def sync_turn(self, *args, **kwargs) -> None:
        """回合结束同步（非阻塞）

        签名兼容基类 MemoryProvider.sync_turn 的不同版本，
        使用 *args/**kwargs 避免参数名不匹配。
        """
        pass

    def shutdown(self) -> None:
        """关闭 provider"""
        if self._engine:
            try:
                self._engine.close()
                self._logger.info("SinoMem 已关闭")
            except Exception as e:
                self._logger.warning(f"关闭异常: {e}")


# ---------------------------------------------------------------------------
# 插件注册
# ---------------------------------------------------------------------------


def register(ctx):
    """注册插件（Hermes 插件加载入口）"""
    ctx.register_memory_provider(SinoMemProvider())
