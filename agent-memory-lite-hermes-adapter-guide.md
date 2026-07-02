# Agent-Memory-Lite × Hermes Memory Provider 适配器安装指南

## 概述

本指南介绍如何将 Agent-Memory-Lite 安装为 Hermes 的 Memory Provider，实现：
- 内置 `memory` 工具写入自动同步到 Agent-Memory-Lite 数据库
- jieba 中文分词 + FTS5 全文搜索
- ONNX 本地语义向量搜索（可选）
- 三种搜索模式：keyword / semantic / hybrid

**架构特点：**
- 只修改 Hermes 侧代码，不需要改动 Agent-Memory-Lite 源码
- 适配器通过 Python 直接调用 Agent-Memory-Lite API（不走 MCP 协议）
- 两边共享同一个 SQLite 数据库（WAL 模式，支持并发访问）

---

## 前置条件

1. **Hermes Agent 已安装**（v0.4+）
2. **Agent-Memory-Lite 项目已部署**（路径：`~/Desktop/Agent-Memory-Lite/`）
3. **Agent-Memory-Lite MCP Server 已配置**（在 `config.yaml` 的 mcp_servers 中）

---

## 安装步骤

### 步骤 1：安装 Python 依赖到 Hermes venv

**⚠️ 关键步骤，跳过会导致适配器加载失败！**

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install jieba tokenizers
```

或使用 uv（推荐）：

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python jieba tokenizers
```

**为什么需要这一步？**
- Agent-Memory-Lite 依赖 jieba 做中文分词
- 适配器在 Hermes 进程中运行，使用 Hermes 的 venv
- 如果依赖缺失，`is_available()` 会抛出 `ImportError` 并返回 False

---

### 步骤 2：创建适配器目录

```bash
mkdir -p ~/.hermes/plugins/agent-memory-lite
```

---

### 步骤 3：创建 plugin.yaml

文件路径：`~/.hermes/plugins/agent-memory-lite/plugin.yaml`

```yaml
name: agent-memory-lite
version: 1.0.0
description: "Agent-Memory-Lite: jieba Chinese FTS5 + ONNX semantic search memory provider"
hooks:
  - on_memory_write
  - on_session_switch
```

---

### 步骤 4：创建适配器代码

文件路径：`~/.hermes/plugins/agent-memory-lite/__init__.py`

```python
"""
Agent-Memory-Lite × Hermes Memory Provider 适配器

功能：
- 包装 agent-memory-lite 的 MemoryEngine
- 提供 memory_search / memory_store / memory_list 工具
- 自动同步内置 memory 工具写入到 agent-memory-lite 数据库
- 支持 jieba 中文分词 + FTS5 搜索 + ONNX 语义搜索
"""

import logging
import sys
import threading
from pathlib import Path
from typing import Any

from agent.memory_provider import MemoryProvider
from tools.registry import tool_error


# ---------------------------------------------------------------------------
# 路径配置
# ---------------------------------------------------------------------------

_USER_NAMESPACE = "_hermes_user_memory"
_AGENT_MEMORY_LITE_DIR = Path.home() / "Desktop" / "Agent-Memory-Lite"
_AGENT_MEMORY_DB = Path.home() / ".agent-memory" / "memory.db"

# 将 agent-memory-lite 添加到 sys.path（确保 import 正功）
if _AGENT_MEMORY_LITE_DIR.is_dir() and str(_AGENT_MEMORY_LITE_DIR) not in sys.path:
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
        """检查 agent-memory-lite 是否可用"""
        try:
            from agent_memory_lite.core.engine import MemoryEngine
            if not _AGENT_MEMORY_DB.exists():
                self._logger.warning(f"数据库不存在: {_AGENT_MEMORY_DB}")
                return False
            return True
        except ImportError as e:
            self._logger.warning(f"agent_memory_lite 导入失败: {e}")
            return False
        except Exception as e:
            self._logger.warning(f"is_available 检查异常: {e}")
            return False

    def initialize(self, session_id: str, **kwargs) -> None:
        """初始化 provider"""
        from agent_memory_lite.core.engine import create_engine

        self._session_id = session_id
        self._hermes_home = kwargs.get("hermes_home", str(Path.home() / ".hermes"))
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
                "description": "搜索长期记忆（中文友好，jieba 分词）。支持三种搜索模式：\n"
                               "• keyword — jieba 中文分词 + FTS5 关键词匹配\n"
                               "• semantic — ONNX 本地语义向量搜索（需嵌入模型）\n"
                               "• hybrid — 关键词 + 语义加权混合排序（推荐）",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "搜索关键词或问题"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["keyword", "semantic", "hybrid"],
                            "description": "搜索模式",
                            "default": "hybrid"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回条数",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "memory_store",
                "description": "存储一条长期记忆。自动去重，自动 jieba 中文分词建索引。"
                               "当用户明确要求记住某事，或你发现值得跨会话保留的信息时使用。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "记忆内容"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["user_pref", "project", "tool", "general"],
                            "description": "分类",
                            "default": "general"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "标签列表"
                        }
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "memory_list",
                "description": "列出已存储的记忆，可按分类过滤。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category": {
                            "type": "string",
                            "enum": ["user_pref", "project", "tool", "general"],
                            "description": "按分类过滤（不填返回全部）"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "返回条数",
                            "default": 20
                        }
                    }
                }
            }
        ]

    def handle_tool_call(self, tool_name: str, arguments: dict) -> str:
        """处理工具调用"""
        import json

        try:
            if tool_name == "memory_search":
                results = self._engine.search(
                    arguments["query"],
                    mode=arguments.get("mode", "hybrid"),
                    limit=arguments.get("limit", 5)
                )
                return json.dumps(results, ensure_ascii=False, default=str)

            elif tool_name == "memory_store":
                result = self._engine.store(
                    content=arguments["content"],
                    category=arguments.get("category", "general"),
                    tags=arguments.get("tags")
                )
                return json.dumps(result, ensure_ascii=False, default=str)

            elif tool_name == "memory_list":
                results = self._engine.list_memories(
                    category=arguments.get("category"),
                    limit=arguments.get("limit", 20)
                )
                return json.dumps(results, ensure_ascii=False, default=str)

            else:
                return tool_error(f"未知工具: {tool_name}")

        except Exception as e:
            self._logger.error(f"工具调用失败 [{tool_name}]: {e}")
            return tool_error(str(e))

    def system_prompt_block(self) -> str:
        """返回系统提示块"""
        try:
            stats = self._engine.stats()
            total = stats.get("total", 0)
            return (
                f"# Agent Memory Lite\n"
                f"Active. {total} memories stored with jieba Chinese tokenization "
                f"and optional semantic search.\n"
                f"Use memory_search to recall context (supports keyword/semantic/hybrid modes).\n"
                f"Use memory_store to persist new information."
            )
        except Exception:
            return "# Agent Memory Lite\nActive (stats unavailable)."

    def on_memory_write(self, action: str, target: str, content: str, metadata: dict | None = None) -> None:
        """
        内置 memory 工具写入时的钩子 — 镜像到 agent-memory-lite
        
        ⚠️ 这是自动同步的核心机制！
        """
        # 跳过非主上下文
        if self._skip_writes:
            return

        # 避免递归：如果当前写入来自 agent-memory-lite 工具，跳过
        # 通过线程局部变量检测
        if getattr(threading.current_thread(), "_agent_memory_lite_writing", False):
            return

        try:
            threading.current_thread()._agent_memory_lite_writing = True
            self._logger.debug(f"on_memory_write: {action} {target}")

            if action in ("add", "replace") and content:
                # 提取分类和标签
                category = "general"
                tags = []

                if metadata:
                    # 尝试从 content 提取分类
                    if "category" in metadata:
                        category = metadata["category"]
                    if "tags" in metadata:
                        tags = metadata["tags"]

                    # 尝试从 tool_call_id 判断是否是 memory_store 工具
                    if "tool_call_id" in metadata:
                        # memory_store 工具会自带 category 和 tags
                        pass

                # 镜像写入
                self._engine.store(
                    content=content,
                    category=category,
                    tags=tags if tags else ["hermes-sync"]
                )
                self._logger.debug(f"同步成功: {content[:50]}...")

        except Exception as e:
            self._logger.warning(f"on_memory_write 同步失败: {e}")
        finally:
            threading.current_thread()._agent_memory_lite_writing = False

    def sync_turn(self, session_id: str, messages: list) -> None:
        """回合结束同步（非阻塞）"""
        # agent-memory-lite 的同步已经在 on_memory_write 中处理
        # 这里不需要额外操作
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
    ctx.register_memory_provider(AgentMemoryLiteProvider)
```

---

### 步骤 5：修改 Hermes 配置

编辑 `~/.hermes/config.yaml`，修改 memory 部分：

```yaml
memory:
  provider: agent-memory-lite  # 从 holographic 改为 agent-memory-lite
  # holographic 相关配置可以删除
```

---

### 步骤 6：删除旧的 holographic 插件（可选）

```bash
rm -rf ~/.hermes/hermes-agent/plugins/memory/holographic/
```

**注意：** 只能有一个外部 memory provider，切换后 holographic 不会再加载。

---

### 步骤 7：重启 Hermes

```bash
# 方式 1：重启网关
hermes gateway restart

# 方式 2：新开 CLI 会话
# 直接运行 hermes 命令即可
```

---

## 验证安装

### 1. 检查 provider 是否加载

启动 Hermes 后，应该在日志中看到：

```
Memory provider 'agent-memory-lite' registered (3 tools)
```

### 2. 验证工具可用

```bash
hermes memory status
```

应该显示：

```
Provider: agent-memory-lite
Tools: memory_search, memory_store, memory_list
```

### 3. 测试同步功能

在 Hermes 中执行：

```
/test memory add "测试记忆：这是一条测试自动同步功能的记忆"
```

然后检查 AML 数据库：

```bash
sqlite3 ~/.agent-memory/memory.db "SELECT * FROM memories ORDER BY id DESC LIMIT 1;"
```

应该能看到刚才写入的记忆。

---

## ⚠️ 常见问题与避坑指南

### 问题 1：Provider 加载失败

**症状：**
```
Memory provider 'holographic' loaded (fallback)
```

**原因：** `agent_memory_lite` 依赖未安装到 Hermes venv

**解决：**
```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python jieba tokenizers
```

---

### 问题 2：ImportError: No module named 'agent_memory_lite'

**症状：**
```
Failed to load provider: No module named 'agent_memory_lite'
```

**原因：** Agent-Memory-Lite 路径未正确添加到 sys.path

**解决：** 检查 `__init__.py` 中的路径配置：

```python
_AGENT_MEMORY_LITE_DIR = Path.home() / "Desktop" / "Agent-Memory-Lite"
```

确保路径指向你的 Agent-Memory-Lite 项目目录。

---

### 问题 3：数据库锁死（database is locked）

**症状：**
```
sqlite3.OperationalError: database is locked
```

**原因：** MCP Server 和适配器同时写入，未使用 WAL 模式

**解决：** 确保 SQLite 使用 WAL 模式：

```bash
sqlite3 ~/.agent-memory/memory.db "PRAGMA journal_mode=WAL;"
```

Agent-Memory-Lite 默认已配置 WAL，如果仍出现此问题，检查 MCP Server 和适配器是否共享同一个数据库路径。

---

### 问题 4：on_memory_write 未触发

**症状：** 内置 memory 工具写入后，AML 数据库中找不到对应记录

**原因：**
1. 适配器未正确注册为 provider
2. `_skip_writes` 被意外设为 True
3. agent_context 不是 "primary"

**解决：**
- 检查日志中是否有 `on_memory_write` 相关输出
- 确认 `config.yaml` 中 `memory.provider: agent-memory-lite`
- 确认当前会话是主上下文（非 cron/subagent）

---

### 问题 5：工具名冲突

**症状：**
```
Tool name 'memory' conflicts with core tool
```

**原因：** 适配器定义了与 Hermes 核心工具同名的工具

**解决：** 确保工具名不与以下保留名冲突：
- `memory`（Hermes 内置记忆工具）
- `todo`（任务管理）
- `session_search`（会话搜索）

本适配器使用的工具名是 `memory_search` / `memory_store` / `memory_list`，不会冲突。

---

### 问题 6：jieba 分词未生效

**症状：** 搜索中文关键词返回 0 条结果

**原因：** jieba 未正确加载或分词配置错误

**解决：**
1. 检查 jieba 是否安装：
   ```bash
   ~/.hermes/hermes-agent/venv/bin/python -c "import jieba; print('OK')"
   ```

2. 重建索引：
   ```bash
   ~/.agent-memory/venv/bin/python -m agent_memory_lite.cli reindex
   ```

---

### 问题 7：MCP 工具和适配器工具重复

**症状：** 同时看到 `mcp_agent_memory_lite_store_memory` 和 `memory_store`

**原因：** MCP Server 和适配器都提供了存储功能

**解决：** 这是正常现象，两种工具可以共存：
- `mcp_agent_memory_lite_*`：直接调用 MCP Server（跨进程）
- `memory_store`：通过适配器调用（进程内，更快）

建议使用 `memory_store`（适配器方式），因为：
1. 更快（无 IPC 开销）
2. 支持自动同步（on_memory_write 钩子）

---

## 文件清单

安装完成后，应该有以下文件：

```
~/.hermes/
├── config.yaml                          # 修改：memory.provider: agent-memory-lite
├── plugins/
│   └── agent-memory-lite/
│       ├── plugin.yaml                  # 新增：插件元数据
│       └── __init__.py                  # 新增：适配器代码（约 250 行）
└── ...

~/Desktop/Agent-Memory-Lite/             # Agent-Memory-Lite 项目（不变）
├── agent_memory_lite/                   # 核心库
├── models/embedding/                    # ONNX 嵌入模型（113MB）
└── ...

~/.agent-memory/
└── memory.db                            # SQLite 数据库（WAL 模式）
```

---

## 卸载方法

如果需要回退到 holographic：

1. 修改 `~/.hermes/config.yaml`：
   ```yaml
   memory:
     provider: holographic
   ```

2. 删除适配器目录：
   ```bash
   rm -rf ~/.hermes/plugins/agent-memory-lite/
   ```

3. 重启 Hermes：
   ```bash
   hermes gateway restart
   ```

---

## 技术细节

### 为什么不需要修改 Agent-Memory-Lite 源码？

Agent-Memory-Lite 已经提供了完整的 Python API：
- `MemoryEngine` 类（store / search / list_memories / stats / close）
- `create_engine()` 工厂函数（自动处理 Embedder 降级）
- SQLite WAL 模式（支持并发访问）

适配器只是在 Hermes 侧包装这些接口，实现了 `MemoryProvider` 的生命周期方法。两边通过 Python 直接调用（import）通信，不走 MCP 协议，所以更快更稳定。

### 数据流

```
用户输入
    ↓
Hermes Agent
    ↓
memory_store 工具调用
    ↓
AgentMemoryLiteProvider.handle_tool_call()
    ↓
MemoryEngine.store()  ←──── 直接调用（进程内）
    ↓
SQLite WAL
    ↓
on_memory_write() 钩子
    ↓
MemoryEngine.store()（镜像写入）
    ↓
~/.agent-memory/memory.db
```

---

## 更新日志

- **2026-07-02**：完成适配器开发和测试
- **2026-07-02**：修复依赖缺失问题（jieba/tokenizers 未安装到 venv）
- **2026-07-02**：验证自动同步功能正常工作

---

**作者：** P1M0U + Hermes Agent  
**版本：** 1.0.0  
**许可：** AGPLv3
