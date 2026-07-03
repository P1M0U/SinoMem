"""
Agent-Memory-Lite × Hermes Memory Provider 适配器

功能：
- 包装 agent-memory-lite 的 MemoryEngine
- 提供 memory_search / memory_store / memory_list 工具
- 自动同步内置 memory 工具写入到 agent-memory-lite 数据库
- 支持 jieba 中文分词 + FTS5 搜索 + ONNX 语义搜索
"""

import importlib
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any

from agent.memory_provider import MemoryProvider  # noqa: E402
from tools.registry import tool_error  # noqa: E402

# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

# 支持 AML_HOME 环境变量覆盖，默认为 ~/Desktop/Agent-Memory-Lite
_AGENT_MEMORY_LITE_DIR = Path(
    os.environ.get("AML_HOME", Path.home() / "Desktop" / "Agent-Memory-Lite")
)
_AGENT_MEMORY_DB = Path.home() / ".agent-memory" / "memory.db"

# 将 agent-memory-lite 添加到 sys.path（确保 import 成功）
if (
    _AGENT_MEMORY_LITE_DIR.is_dir()
    and str(_AGENT_MEMORY_LITE_DIR) not in sys.path
):
    sys.path.insert(0, str(_AGENT_MEMORY_LITE_DIR))


# ---------------------------------------------------------------------------
# Provider 实现
# ---------------------------------------------------------------------------


class AgentMemoryLiteProvider(MemoryProvider):
    """Hermes Memory Provider 适配器 — 包装 agent-memory-lite"""

    name = "agent-memory-lite"

    def __init__(self):
        self._engine = None
        self._session_id = None
        self._hermes_home = None
        self._agent_context = None
        self._skip_writes = False  # cron/subagent 不镜像写入
        self._logger = logging.getLogger("hermes.memory.agent-memory-lite")

    def is_available(self) -> bool:
        """检查 agent-memory-lite 是否可用

        仅检查核心库是否可导入 + 项目目录是否存在。
        数据库文件由 initialize() -> create_engine() 自动创建，无需预先存在。
        """
        try:
            if importlib.util.find_spec("agent_memory_lite") is None:
                self._logger.warning(
                    "agent_memory_lite 未安装或不在 sys.path 中"
                )
                return False
            if not _AGENT_MEMORY_LITE_DIR.is_dir():
                self._logger.warning(
                    f"项目目录不存在: {_AGENT_MEMORY_LITE_DIR}\n"
                    "可通过环境变量 AML_HOME 指定路径"
                )
                return False
            return True
        except Exception as e:
            self._logger.warning(f"is_available 检查异常: {e}")
            return False

    def get_config_schema(self) -> dict:
        """返回 provider 配置项说明，供 hermes memory status 展示"""
        return {
            "aml_home": {
                "type": "path",
                "description": "Agent-Memory-Lite 项目目录路径",
                "default": str(Path.home() / "Desktop" / "Agent-Memory-Lite"),
            },
            "db_path": {
                "type": "path",
                "description": "SQLite 数据库路径",
                "default": str(_AGENT_MEMORY_DB),
            },
        }

    def initialize(self, session_id: str, **kwargs) -> None:
        """初始化 provider"""
        from agent_memory_lite.core.engine import create_engine

        self._session_id = session_id
        self._hermes_home = kwargs.get(
            "hermes_home", str(Path.home() / ".hermes")
        )
        self._agent_context = kwargs.get("agent_context", "primary")

        # 非主上下文（cron/subagent）不镜像写入
        if self._agent_context != "primary":
            self._skip_writes = True

        try:
            self._engine = create_engine(str(_AGENT_MEMORY_DB))
            self._logger.info(
                f"AgentMemoryLite 初始化成功 (session={session_id}, "
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
            return "# Agent Memory Lite\nInitializing..."
        try:
            stats = self._engine.stats()
            total = stats.get("total", 0)
            return (
                "# Agent Memory Lite\n"
                f"Active. {total} memories stored with jieba Chinese tokenization "
                "and optional semantic search.\n"
                "Use memory_search to recall context (supports keyword/semantic/hybrid modes).\n"
                "Use memory_store to persist new information."
            )
        except Exception:
            return "# Agent Memory Lite\nActive (stats unavailable)."

    def on_memory_write(
        self,
        action: str,
        target: str,
        content: str,
        metadata: dict | None = None,
    ) -> None:
        """
        内置 memory 工具写入时的钩子 — 镜像到 agent-memory-lite

        ⚠️ 这是自动同步的核心机制！
        """
        # 跳过非主上下文
        if self._skip_writes:
            return

        # 避免递归：如果当前写入来自 agent-memory-lite 工具，跳过
        if getattr(
            threading.current_thread(), "_agent_memory_lite_writing", False
        ):
            return

        try:
            threading.current_thread()._agent_memory_lite_writing = True
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
            threading.current_thread()._agent_memory_lite_writing = False

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
                self._logger.info("AgentMemoryLite 已关闭")
            except Exception as e:
                self._logger.warning(f"关闭异常: {e}")


# ---------------------------------------------------------------------------
# 插件注册
# ---------------------------------------------------------------------------


def register(ctx):
    """注册插件（Hermes 插件加载入口）"""
    ctx.register_memory_provider(AgentMemoryLiteProvider())
