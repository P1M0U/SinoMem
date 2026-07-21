# SinoMem × Hermes Memory Provider 适配器安装指南

## 概述

本指南介绍如何将 SinoMem 安装为 Hermes 的 Memory Provider，实现：
- 内置 `memory` 工具写入自动同步到 SinoMem 数据库
- jieba 中文分词 + FTS5 全文搜索
- ONNX 本地语义向量搜索（可选）
- 三种搜索模式：keyword / semantic / hybrid

**架构特点：**
- 只修改 Hermes 侧代码，不需要改动 SinoMem 源码
- 适配器通过 Python 直接调用 SinoMem API（不走 MCP 协议）
- 两边共享同一个 SQLite 数据库（WAL 模式，支持并发访问）

---

## 前置条件

1. **Hermes Agent 已安装**（v0.4+）
2. **SinoMem 已安装**（路径：`~/.local/share/sinomem/`）

---

## 安装步骤

> **💡 如果你使用了一键安装脚本（`install.sh`），以下步骤已自动完成，可直接跳到验证部分。**

### 步骤 1：安装 Python 依赖和 sinomem 到 Hermes venv

**⚠️ 关键步骤，跳过会导致适配器加载失败！**

适配器在 Hermes 进程中运行，使用 Hermes 自己的 venv，需要将三个依赖装进去：

```bash
# 先升级 pip（避免旧版与 setuptools-scm 不兼容）
~/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade pip

# 安装轻量依赖
~/.hermes/hermes-agent/venv/bin/python -m pip install jieba tokenizers

# 安装 sinomem 包本身（可编辑模式，git pull 即可更新）
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ~/.local/share/sinomem
```

**为什么需要安装 sinomem 本身？**
- 适配器从 `sinomem.plugins.hermes.provider` 导入核心实现
- 仅安装 jieba + tokenizers 不够，`is_available()` 中的 `find_spec("sinomem")` 会返回 None
- 通过 `pip install -e` 安装后，`import sinomem` 才能在 Hermes venv 中正常工作

---

### 步骤 2：链接适配器插件

适配器代码已内置在 SinoMem 项目的 `hermes_plugin/` 目录中：

```bash
ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem
```

> 使用符号链接而非复制：`git pull` 更新项目后插件自动同步，无需再次操作。

---

### 步骤 3：修改 Hermes 配置

编辑 `~/.hermes/config.yaml`，修改 memory 部分：

```yaml
memory:
  provider: sinomem  # 从 holographic 改为 sinomem
```

---

### 步骤 4：删除旧的 holographic 插件（可选）

```bash
rm -rf ~/.hermes/hermes-agent/plugins/memory/holographic/
```

**注意：** 只能有一个外部 memory provider，切换后 holographic 不会再加载。

---

### 步骤 5：重启 Hermes

```bash
hermes gateway restart
```

---

## 验证安装

### 1. 检查 provider 是否加载

启动 Hermes 后，应该在日志中看到：

```
Memory provider 'sinomem' registered (3 tools)
```

### 2. 验证工具可用

```bash
hermes memory status
```

应该显示：

```
Provider: sinomem
Tools: memory_search, memory_store, memory_list
```

### 3. 测试同步功能

在 Hermes 中执行：

```
/test memory add "测试记忆：这是一条测试自动同步功能的记忆"
```

然后检查 AML 数据库：

```bash
sqlite3 ~/.sinomem/memory.db "SELECT * FROM memories ORDER BY id DESC LIMIT 1;"
```

应该能看到刚才写入的记忆。

---

## ⚠️ 常见问题与避坑指南

### 问题 1：Provider 加载失败

**症状：**
```
Memory provider 'holographic' loaded (fallback)
```

**原因：** sinomem 未安装到 Hermes venv

**解决：**
```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install --upgrade pip
~/.hermes/hermes-agent/venv/bin/python -m pip install jieba tokenizers
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ~/.local/share/sinomem
```

---

### 问题 2：ImportError: No module named 'sinomem'

**症状：**
```
Failed to load provider: No module named 'sinomem'
```

**原因：** sinomem 包未安装到 Hermes venv（这是最常见的问题）

**解决：** 将 sinomem 安装到 Hermes venv：

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install -e ~/.local/share/sinomem
```

---

### 问题 3：数据库锁死（database is locked）

**症状：**
```
sqlite3.OperationalError: database is locked
```

**原因：** MCP Server 和适配器同时写入，未使用 WAL 模式

**解决：** 确保 SQLite 使用 WAL 模式：

```bash
sqlite3 ~/.sinomem/memory.db "PRAGMA journal_mode=WAL;"
```

SinoMem 默认已配置 WAL。

---

### 问题 4：on_memory_write 未触发

**症状：** 内置 memory 工具写入后，AML 数据库中找不到对应记录

**原因：**
1. 适配器未正确注册为 provider
2. `_skip_writes` 被意外设为 True
3. agent_context 不是 "primary"

**解决：**
- 检查日志中是否有 `on_memory_write` 相关输出
- 确认 `config.yaml` 中 `memory.provider: sinomem`
- 确认当前会话是主上下文（非 cron/subagent）

---

### 问题 5：jieba 分词未生效

**症状：** 搜索中文关键词返回 0 条结果

**原因：** jieba 未正确加载或分词配置错误

**解决：**
1. 检查 jieba 是否安装：
   ```bash
   ~/.hermes/hermes-agent/venv/bin/python -c "import jieba; print('OK')"
   ```
2. 重建索引：
   ```bash
   sinomem reindex
   ```

---

### 问题 6：MCP 工具和适配器工具重复

**症状：** 同时看到 `mcp_sinomem_store_memory` 和 `memory_store`

**原因：** MCP Server 和适配器都提供了存储功能

**解决：** 这是正常现象，两种工具可以共存。建议使用 `memory_store`（适配器方式），因为：
1. 更快（无 IPC 开销）
2. 支持自动同步（on_memory_write 钩子）

---

## 文件清单

安装完成后，应该有以下文件：

```
~/.hermes/
├── config.yaml                                # 修改：memory.provider: sinomem
├── plugins/
│   └── sinomem/
│       ├── plugin.yaml                        # 插件元数据（从 hermes_plugin/ 复制）
│       └── __init__.py                        # 重导出入口
└── ...

~/.local/share/sinomem/
├── sinomem/                         # 核心库
│   └── plugins/hermes/
│       └── provider.py                        # Hermes 适配器核心实现
├── hermes_plugin/                             # Hermes 插件入口
│   ├── plugin.yaml                            # 插件元数据（Hermes 发现入口）
│   └── __init__.py                            # 重导出到 sinomem.plugins.hermes
├── models/embedding/                          # ONNX 嵌入模型（可选）
└── ...

~/.sinomem/
└── memory.db                                  # SQLite 数据库（WAL 模式）
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
   rm -rf ~/.hermes/plugins/sinomem/
   ```
3. 重启 Hermes：
   ```bash
   hermes gateway restart
   ```

---

## 技术细节

### 为什么不需要修改 SinoMem 源码？

SinoMem 已经提供了完整的 Python API：
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
SinoMemProvider.handle_tool_call()
    ↓
MemoryEngine.store()  ←──── 直接调用（进程内）
    ↓
SQLite WAL
    ↓
on_memory_write() 钩子
    ↓
MemoryEngine.store()（镜像写入）
    ↓
~/.sinomem/memory.db
```

---

## 更新日志

- **2026-07-17**：核心实现迁移至 `sinomem/plugins/hermes/provider.py`，`hermes_plugin/` 改为薄层重导出
- **2026-07-02**：完成适配器开发和测试
- **2026-07-02**：修复依赖缺失问题（jieba/tokenizers 未安装到 venv）
- **2026-07-02**：验证自动同步功能正常工作
- **2026-07-02**：适配器代码从文档内嵌改为项目 `hermes_plugin/` 目录统一管理，安装简化为 `cp -r`

---

**作者：** P1M0U
**版本：** 1.0.0
**许可：** Apache 2.0
