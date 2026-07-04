# Agent Memory Lite

[English](README_EN.md) | 中文

> v0.6.0

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-中文分词-blue)
![ONNX](https://img.shields.io/badge/ONNX-推理-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-向量搜索-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-包管理-orange)
![License](https://img.shields.io/badge/License-AGPLv3-blue)
![Platform](https://img.shields.io/badge/平台-Claude%20Code%20|%20Cursor%20|%20Cline%20|%20Hermes-purple)
![模型可选](https://img.shields.io/badge/嵌入模型-可选,~24MB起-lightgrey)
![Stars](https://img.shields.io/github/stars/P1M0U/Agent-Memory-Lite?style=social)

> 让你的 AI Agent 拥有永不遗忘的长期记忆。
> 一行命令接入，零 API 费用，数据 100% 本地存储。

轻量级中文友好的 Agent 记忆增强系统，支持 SQLite + FTS5 + jieba 分词 + 本地 ONNX 向量搜索，零 API 调用。可通过 MCP 协议接入 Claude Code、Cursor、Cline、Hermes 等任意 Agent。

## 快速体验（30 秒上手）

```bash
git clone https://github.com/P1M0U/Agent-Memory-Lite.git && cd Agent-Memory-Lite
uv sync

# 存一条记忆，搜一条记忆
uv run aml store "用户偏好使用 Docker 部署" -c user_pref
uv run aml search "Docker"
# 输出: #1  user_pref
#        用户偏好使用 Docker 部署
```

## 适用场景

- 🤖 用 Claude Code / Cursor / Cline / Hermes 等 AI 编程助手的开发者
- 🇨🇳 需要高质量中文分词的记忆场景（jieba 定制分词）
- 🔒 数据不能上云的合规要求（100% 本地 SQLite 存储）
- 💰 不想为 Embedding API 付费的团队（本地 ONNX 推理）
- 🔗 多个 AI 工具之间共享同一份长期记忆

## 为什么选择 Agent Memory Lite？

| 对比维度 | Agent Memory Lite | Mem0 | 内置记忆 |
|---------|-------------------|------|---------|
| 中文分词 | ✅ jieba 定制 | 默认分词 | 默认分词 |
| 本地部署 | ✅ SQLite 单文件 | ❌ 需 API | ✅ 绑定框架 |
| 嵌入模型 | ✅ ONNX 本地 ~24MB | OpenAI API | 无 |
| MCP 协议 | ✅ 标准 MCP Server | ❌ | ❌ |
| 跨 Agent 共享 | ✅ 一份 .db 通用 | ❌ | ❌ |
| 数据库可备份 | ✅ 单文件复制即可 | ❌ | ❌ |
| 费用 | 💰 零 API 费用 | 💰💸 按 token 计费 | 💰 零 |

## 特性

- **中文 FTS5 搜索** — jieba 分词 + SQLite FTS5，写入和查询用同一套分词器，token 完全对齐
- **语义搜索** — 本地 ONNX 嵌入模型（~24MB 起），可选安装，支持双模自动识别
- **混合搜索** — 关键词 + 语义加权排序，兼顾精确和模糊
- **MCP Server** — 标准协议，10 个工具，可接入任何支持 MCP 的 Agent
- **Hermes Memory Provider 插件** — 进程内直接调用，自动同步内置 memory 工具写入，工具不重复
- **CLI 工具** — 10 个子命令（store / search / get / update / delete / list / stats / vacuum / clean / reindex）
- **数据迁移** — 支持从 holographic memory 导入，支持为已有记忆补充向量
- **自动去重** — 默认跳过重复内容
- **数据库维护** — VACUUM 回收空间、reindex 重建索引、clean 批量删除
- **内容安全防护** — 自动截断超长内容（8000 字符）
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
hermes_plugin/      # Hermes Memory Provider 适配器插件
models/embedding/   # ONNX 嵌入模型（需单独下载）
```

---

## 一键安装（给智能体的提示词）

复制以下内容发给你的 AI Agent，它会自动完成克隆、安装、配置。

> **💡 如果你使用的是 Hermes Agent**，推荐通过 **Memory Provider 插件方式**安装，可获得更好的集成体验（自动同步、进程内调用、工具去重）。详见 [Hermes Memory Provider 适配器安装指南](agent-memory-lite-hermes-adapter-guide.md)。

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

4. 询问用户是否需要下载嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不下载（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. paraphrase-multilingual-MiniLM-L12-v2（~113MB，384 维，50+ 语言，适合多语言混用）
   — C. bge-small-zh-v1.5（~24MB，512 维，中文优化，适合纯中文场景，体积更小）
   如果用户选择 B 或 C，从 hf-mirror.com 镜像下载对应模型到 models/embedding/ 目录

5. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`，然后按 [适配器安装指南](agent-memory-lite-hermes-adapter-guide.md) 完成剩余步骤（步骤 6-8 不需要执行）
   — B. MCP Server 方式 — 继续执行以下步骤 6-8

6. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段（请将 /home/你的用户名 替换为实际路径）：
   agent-memory-lite:
     args: []
     command: /home/你的用户名/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

7. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

8. 给 wrapper 脚本加执行权限
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

4. 询问用户是否需要下载嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不下载（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. paraphrase-multilingual-MiniLM-L12-v2（~113MB，384 维，50+ 语言，适合多语言混用）
   — C. bge-small-zh-v1.5（~24MB，512 维，中文优化，适合纯中文场景，体积更小）
   如果用户选择 B 或 C，从 hf-mirror.com 镜像下载对应模型到 models/embedding/ 目录

5. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`，然后按 [适配器安装指南](agent-memory-lite-hermes-adapter-guide.md) 完成剩余步骤（步骤 6-8 不需要执行）
   — B. MCP Server 方式 — 继续执行以下步骤 6-8

6. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段（请将 /home/你的用户名 替换为实际路径）：
   agent-memory-lite:
     args: []
     command: /home/你的用户名/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

7. 创建 wrapper 脚本 ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh，内容：
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

8. 给 wrapper 脚本加执行权限
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

本项目支持两种嵌入模型，根据你的场景选择其中一个下载即可（系统会自动识别模型类型）：

| 模型 | 大小 | 维度 | 语言 | 适用场景 |
|------|------|------|------|----------|
| **paraphrase-multilingual-MiniLM-L12-v2** | ~113MB | 384 | 50+ 语言 | 多语言混用、中英夹杂内容多 |
| **bge-small-zh-v1.5** | ~24MB | 512 | 中文优化 | 纯中文为主、追求更小体积和更好中文效果 |

```bash
# 创建模型目录
mkdir -p models/embedding/onnx

# 安装下载工具
pip install huggingface-hub

# ─── 模型 A：paraphrase-multilingual-MiniLM-L12-v2（多语言，~113MB）───
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding')
hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')
"

# ─── 模型 B：bge-small-zh-v1.5（中文优化，~24MB）───
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('Xenova/bge-small-zh-v1.5', 'onnx/model_quantized.onnx', local_dir='models/embedding')
hf_hub_download('Xenova/bge-small-zh-v1.5', 'tokenizer.json', local_dir='models/embedding')
"
```

> **💡 国内用户**：下载前设置环境变量 `HF_ENDPOINT=https://hf-mirror.com` 使用镜像加速。

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
