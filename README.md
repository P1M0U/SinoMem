# Agent Memory Lite

[English](README_EN.md) | 中文

> v0.5.8

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-中文分词-blue)
![ONNX](https://img.shields.io/badge/ONNX-推理-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-向量搜索-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-包管理-orange)
![License](https://img.shields.io/badge/License-AGPLv3-blue)

轻量级中文友好的 Agent 记忆增强系统。基于 SQLite + FTS5 + jieba 分词 + 本地 ONNX 向量搜索，零 API 调用。

## 设计初衷

### 与 Agent 内置记忆的区别

Agent 框架（如 Claude Code）通常自带会话级记忆来处理**当前会话内的上下文**。本项目解决的是另一个层次的问题：

| 维度 | Agent 内置记忆 | Agent Memory Lite |
|------|---------------|-------------------|
| **记忆范围** | 会话级上下文 | 跨会话长期记忆 |
| **搜索方式** | FTS5（框架默认分词） | FTS5（jieba 定制中文分词） |
| **语义搜索** | 无 | 可选 ONNX 本地语义搜索 |
| **自动去重** | 无 | 默认开启 |
| **批量删除** | 无 | 按分类批量 + 清空 |
| **数据独立性** | 绑定框架，无法外部访问 | 独立 `.db` 文件，可备份迁移 |
| **多 Agent 共享** | 不适用 | 同一份记忆供多个 Agent 读写 |

### 跨 Agent 记忆中枢

本项目的独特价值在于**不绑定任何 Agent 框架**。同一份 `.db` 文件可以被多个 MCP 兼容的 Agent（如 Claude Code、Claude Desktop、Cursor、Cline 等）共享：

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Claude   │  │ Cursor   │  │ Cline    │  ... 任意 MCP 兼容 Agent
│  Code    │  │          │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │ MCP 协议 (stdio)
            ┌──────┴──────┐
            │ Agent Memory │
            │     Lite     │
            └──────┬──────┘
                   │
            ┌──────┴──────┐
            │  memory.db  │  独立存储，可备份 / 迁移 / 分析
            └─────────────┘
```

这意味着：
- 用 Claude Code 记下的事，切换到 Cursor 后仍然可查
- 一个 IDE 学到的用户偏好，在另一个 IDE 中也能利用
- 记忆数据独立于工具版本，不会因升级丢失
- 一份记忆在多个开发工具间形成真正的"跨工具长期知识库"

## 特性

- **中文 FTS5 搜索** — jieba 分词 + SQLite FTS5，写入和查询用同一套分词器，token 完全对齐
- **语义搜索** — 本地 ONNX 嵌入模型（~113MB），可选安装，不依赖外部服务
- **批量嵌入推理** — ONNX Runtime batch 推理，大规模记忆导入性能更好
- **混合搜索** — 关键词 + 语义加权排序，兼顾精确和模糊
- **MCP Server** — 标准协议，10 个工具，可接入任何支持 MCP 的 Agent
- **CLI 工具** — 10 个子命令（store / search / get / update / delete / list / stats / vacuum / clean / reindex），方便脚本集成
- **数据迁移** — 支持从 holographic memory 导入，支持为已有记忆补充向量
- **内容安全防护** — 自动截断超长内容（8000 字符），防止搜索质量下降
- **自动去重** — 默认跳过重复内容，可通过参数关闭
- **数据库维护** — VACUUM 回收空间、reindex 重建索引、clean 批量删除
- **线程安全** — check_same_thread=False，支持多 Agent 并发访问

---

## 项目结构

```
agent_memory_lite/
├── core/           # 核心业务逻辑（存储、搜索、分词、嵌入）
├── entrypoints/    # 对外入口（CLI 和 MCP Server）
└── tools/          # 数据迁移工具
tests/              # 测试
dicts/              # 自定义 jieba 词典
models/embedding/   # ONNX 嵌入模型（需单独下载）
```

---

## 一键安装（给智能体的提示词）

复制以下内容发给你的 AI Agent，它会自动完成克隆、安装、配置：

### 方式一：从 GitHub 安装

```
请帮我安装 Agent Memory Lite 记忆系统，步骤如下：

1. 克隆仓库到 ~/Desktop/Agent-Memory-Lite/
   git clone https://github.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. 进入项目目录，用 uv 安装依赖（使用清华镜像加速）
   cd ~/Desktop/Agent-Memory-Lite
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

3. 验证安装是否成功
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. 询问用户是否需要下载嵌入模型（paraphrase-multilingual-MiniLM-L12-v2，约 113MB）
   — 如果用户选择下载，则从 hf-mirror.com 下载 ONNX 量化模型到 models/embedding/ 目录，用于语义搜索
   — 如果用户选择不下载，跳过此步骤；不下载模型时不报错，语义搜索自动降级为关键词搜索

5. 把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段（请将 /home/你的用户名 替换为实际路径）：
   agent-memory-lite:
     args: []
     command: /home/你的用户名/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

6. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

7. 给 wrapper 脚本加执行权限
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

完成后告诉我安装结果。
```

### 方式二：从 Gitee 安装（国内更快）

```
请帮我安装 Agent Memory Lite 记忆系统，步骤如下：

1. 克隆仓库到 ~/Desktop/Agent-Memory-Lite/
   git clone https://gitee.com/pimou/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. 进入项目目录，用 uv 安装依赖（使用清华镜像加速）
   cd ~/Desktop/Agent-Memory-Lite
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

3. 验证安装是否成功
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. 询问用户是否需要下载嵌入模型（paraphrase-multilingual-MiniLM-L12-v2，约 113MB）
   — 如果用户选择下载，则从 hf-mirror.com 下载 ONNX 量化模型到 models/embedding/ 目录，用于语义搜索
   — 如果用户选择不下载，跳过此步骤；不下载模型时不报错，语义搜索自动降级为关键词搜索

5. 把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段（请将 /home/你的用户名 替换为实际路径）：
   agent-memory-lite:
     args: []
     command: /home/你的用户名/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

6. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

7. 给 wrapper 脚本加执行权限
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

完成后告诉我安装结果。
```

---

## 手动安装

```bash
# 1. 克隆
git clone https://github.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite
cd ~/Desktop/Agent-Memory-Lite

# 2. 安装依赖
uv sync

# 3. 验证
uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"
```

## 下载嵌入模型（可选，用于语义搜索）

嵌入模型约 113MB，需单独下载：

```bash
# 创建模型目录
mkdir -p models/embedding/onnx

# 下载模型文件（二选一）
# 方式一：从 HuggingFace 下载
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding'); hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')"

# 方式二：从 hf-mirror.com 下载（国内更快）
HF_ENDPOINT=https://hf-mirror.com python -c "from huggingface_hub import hf_hub_download; hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding'); hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')"
```

不下载模型也能使用，语义搜索会自动降级为关键词搜索。

## 手动配置 Hermes MCP

在 `~/.hermes/config.yaml` 的 `mcp_servers:` 下添加：

```yaml
  agent-memory-lite:
    args: []
    command: /home/你的用户名/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```
（请将 `/home/你的用户名` 替换为实际 home 路径）

创建 wrapper 脚本：

```bash
cat > ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh << 'EOF'
#!/bin/bash
cd ~/Desktop/Agent-Memory-Lite
exec uv run python -m agent_memory_lite.entrypoints.mcp_server
EOF
chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

重启 Hermes 后生效。

---

## 使用方法

### CLI 命令行

```bash
# 存储记忆
uv run python -m agent_memory_lite.entrypoints.cli store "用户偏好飞书发送文件" -c user_pref -t "飞书"

# 关键词搜索
uv run python -m agent_memory_lite.entrypoints.cli search "飞书"

# 语义搜索
uv run python -m agent_memory_lite.entrypoints.cli search "怎么给用户传东西" -m semantic

# 混合搜索
uv run python -m agent_memory_lite.entrypoints.cli search "MCP协议" -m hybrid

# 查看统计
uv run python -m agent_memory_lite.entrypoints.cli stats

# 列出所有记忆
uv run python -m agent_memory_lite.entrypoints.cli list

# 回收已删除的磁盘空间
uv run python -m agent_memory_lite.entrypoints.cli vacuum
```

### MCP Server（Agent 自动调用）

配置完成后，Agent 可以直接调用以下 9 个工具：

| 工具名 | 说明 |
|--------|------|
| `store_memory` | 存储一条记忆（支持去重） |
| `search_memory` | 搜索记忆（keyword/semantic/hybrid） |
| `get_memory` | 获取指定记忆 |
| `update_memory` | 更新记忆 |
| `delete_memory` | 删除记忆 |
| `delete_memories_by_category` | 按分类批量删除 |
| `list_memories` | 列出记忆 |
| `memory_stats` | 查看统计 |
| `reindex_memories` | 重建 FTS5 分词索引 |

### 数据迁移

```bash
# 从 holographic memory 导入
uv run python -m agent_memory_lite.entrypoints.cli import

# 预览（不实际写入）
uv run python -m agent_memory_lite.entrypoints.cli import --dry-run

# 为已有记忆生成向量嵌入
uv run python -m agent_memory_lite.entrypoints.cli migrate
```

### 数据库维护

```bash
# 回收已删除记忆占用的磁盘空间
uv run python -m agent_memory_lite.entrypoints.cli vacuum
```

大量删除记忆后，SQLite 不会自动回收空间。`vacuum` 命令会重建数据库文件，释放已删除的磁盘空间。

---

## 搜索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `keyword` | FTS5 关键词匹配 | 精确查找，如搜"飞书" |
| `semantic` | 向量语义相似度 | 模糊查找，如搜"怎么传文件" |
| `hybrid` | 关键词 + 语义加权 | 通用场景，兼顾精确和模糊 |

## License

[AGPLv3](LICENSE)

Copyright © 2026 [P1M0U](https://github.com/P1M0U)

---

## 联系作者

- 电子邮箱：[p1m0u@foxmail.com](mailto:p1m0u@foxmail.com)
- GitHub：[https://github.com/P1M0U/Agent-Memory-Lite](https://github.com/P1M0U/Agent-Memory-Lite)
- Gitee：[https://gitee.com/pimou/Agent-Memory-Lite](https://gitee.com/pimou/Agent-Memory-Lite)
