# Agent Memory Lite

[English](README_EN.md) | 中文

> v0.2.0

轻量级中文友好的 Agent 记忆增强系统。基于 SQLite + FTS5 + 本地向量搜索，零 API 调用。

## 特性

- **中文 FTS5 搜索** — jieba 分词 + SQLite FTS5，零 API 调用
- **语义搜索** — 本地 ONNX 嵌入模型（~113MB），不依赖外部服务
- **混合搜索** — 关键词 + 语义加权排序
- **MCP Server** — 标准协议，可接入任何支持 MCP 的 Agent
- **CLI 工具** — 命令行操作，方便脚本集成
- **数据迁移** — 支持从 holographic memory 导入

---

## 一键安装（给智能体的提示词）

复制以下内容发给你的 AI Agent，它会自动完成克隆、安装、配置：

### 方式一：从 GitHub 安装

```
请帮我安装 Agent Memory Lite 记忆系统，步骤如下：

1. 克隆仓库到 ~/Desktop/Agent-Memory-Lite/
   git clone git@github.com:P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. 进入项目目录，用 uv 安装依赖
   cd ~/Desktop/Agent-Memory-Lite
   uv sync

3. 验证安装是否成功
   uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"

4. 把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.mcp_server

6. 给 wrapper 脚本加执行权限
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

完成后告诉我安装结果。
```

### 方式二：从 Gitee 安装（国内更快）

```
请帮我安装 Agent Memory Lite 记忆系统，步骤如下：

1. 克隆仓库到 ~/Desktop/Agent-Memory-Lite/
   git clone git@gitee.com:pimou/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. 进入项目目录，用 uv 安装依赖
   cd ~/Desktop/Agent-Memory-Lite
   uv sync

3. 验证安装是否成功
   uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"

4. 把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.mcp_server

6. 给 wrapper 脚本加执行权限
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

完成后告诉我安装结果。
```

---

## 手动安装

```bash
# 1. 克隆
git clone git@github.com:P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite
cd ~/Desktop/Agent-Memory-Lite

# 2. 安装依赖
uv sync

# 3. 验证
uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"
```

## 手动配置 Hermes MCP

在 `~/.hermes/config.yaml` 的 `mcp_servers:` 下添加：

```yaml
  agent-memory-lite:
    args: []
    command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

创建 wrapper 脚本：

```bash
cat > ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh << 'EOF'
#!/bin/bash
cd ~/Desktop/Agent-Memory-Lite
exec uv run python -m agent_memory_lite.mcp_server
EOF
chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

重启 Hermes 后生效。

---

## 使用方法

### CLI 命令行

```bash
# 存储记忆
uv run python -m agent_memory_lite.cli store "用户偏好飞书发送文件" -c user_pref -t "飞书"

# 关键词搜索
uv run python -m agent_memory_lite.cli search "飞书"

# 语义搜索
uv run python -m agent_memory_lite.cli search "怎么给用户传东西" -m semantic

# 混合搜索
uv run python -m agent_memory_lite.cli search "MCP协议" -m hybrid

# 查看统计
uv run python -m agent_memory_lite.cli stats

# 列出所有记忆
uv run python -m agent_memory_lite.cli list
```

### MCP Server（Agent 自动调用）

配置完成后，Agent 可以直接调用以下 7 个工具：

| 工具名 | 说明 |
|--------|------|
| `store_memory` | 存储一条记忆 |
| `search_memory` | 搜索记忆（keyword/semantic/hybrid） |
| `get_memory` | 获取指定记忆 |
| `update_memory` | 更新记忆 |
| `delete_memory` | 删除记忆 |
| `list_memories` | 列出记忆 |
| `memory_stats` | 查看统计 |

### 数据迁移

```bash
# 从 holographic memory 导入
uv run python -m agent_memory_lite.cli import

# 预览（不实际写入）
uv run python -m agent_memory_lite.cli import --dry-run

# 为已有记忆生成向量嵌入
uv run python -m agent_memory_lite.cli migrate
```

---

## 搜索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `keyword` | FTS5 关键词匹配 | 精确查找，如搜"飞书" |
| `semantic` | 向量语义相似度 | 模糊查找，如搜"怎么传文件" |
| `hybrid` | 关键词 + 语义加权 | 通用场景，兼顾精确和模糊 |

## 技术栈

```
语言：Python 3.11+
包管理：uv
MCP 协议：fastmcp 3.x
存储：SQLite + FTS5
中文分词：jieba + 自定义词典
向量搜索：sqlite-vec
嵌入模型：ONNX 量化版（paraphrase-multilingual-MiniLM-L12-v2）
CLI：click
```

## License

MIT
