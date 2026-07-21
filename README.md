# SinoMem

[English](README_EN.md) | 中文

> v0.6.9

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-中文分词-blue)
![ONNX](https://img.shields.io/badge/ONNX-推理-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-向量搜索-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-包管理-orange)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

> 让你的 AI Agent 拥有永不遗忘的长期记忆。
> 一行命令接入，零 API 费用，数据 100% 本地存储。

轻量级中文友好的 Agent 记忆增强系统，支持 SQLite + FTS5 + jieba 分词 + 本地 ONNX 向量搜索，零 API 调用。可通过 MCP 协议接入 Claude Code、Cursor、Cline、Hermes 等任意 Agent。

## 快速体验（30 秒上手）

```bash
# 国内用户（Gitee，推荐）
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash

# 或 GitHub 用户
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# 安装后打开新终端，即可使用：
sinomem store "用户偏好使用 Docker 部署" -c user_pref
sinomem search "Docker"
# 输出: #1  user_pref  score=0.2
#        用户偏好使用 Docker 部署
```

> 安装到 `~/.local/share/sinomem/`，不会污染 Desktop 目录。安装后可直接使用 `sinomem` 命令。

## 适用场景

- 🤖 用 Claude Code / Cursor / Cline / Hermes 等 AI 编程助手的开发者
- 🇨🇳 需要高质量中文分词的记忆场景（jieba 定制分词）
- 🔒 数据不能上云的合规要求（100% 本地 SQLite 存储）
- 💰 不想为 Embedding API 付费的团队（本地 ONNX 推理）
- 🔗 多个 AI 工具之间共享同一份长期记忆

## 为什么选择 SinoMem？

| 对比维度 | SinoMem | Mem0 | 内置记忆 |
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
- **MCP Server** — 标准协议，12 个工具，可接入任何支持 MCP 的 Agent
- **多 Agent 自动同步插件** — Claude Code / LangChain / CrewAI / AutoGen / Hermes 开箱即用
- **CLI 工具** — 15 个子命令（store / search / get / update / delete / list / stats / vacuum / clean / reindex / cleanup / migrate / import / store-batch / search-batch）
- **数据迁移** — 支持从 holographic memory 导入，支持为已有记忆补充向量
- **自动去重** — 默认跳过重复内容
- **数据库维护** — VACUUM 回收空间、reindex 重建索引、clean 批量删除
- **内容安全防护** — 自动截断超长内容（8000 字符）
- **线程安全** — check_same_thread=False，支持多 Agent 并发访问

---

## 项目结构

```
sinomem/        # 核心记忆引擎
├── core/                 # 存储、搜索、分词、嵌入
├── dicts/                # 自定义 jieba 词典
├── entrypoints/          # CLI 和 MCP Server
├── plugins/              # 多 Agent 自动同步插件
│   ├── base.py           # 插件基类（auto_store / auto_search / inject_context）
│   ├── claude_code/      # Claude Code 钩子插件
│   ├── langchain/        # LangChain BaseMemory 组件
│   ├── crewai/           # CrewAI Memory 组件（WIP）
│   ├── autogen/          # AutoGen memory_provider（WIP）
│   └── hermes/           # Hermes MemoryProvider 核心实现
│       └── provider.py   # on_memory_write 自动同步
└── tools/                # 数据迁移工具
hermes_plugin/            # Hermes 插件入口（plugin.yaml + 重导出）
installers/               # Claude Code 自动安装脚本
tests/                    # 测试
models/embedding/         # ONNX 嵌入模型（自动下载）
install.sh                # 一键安装脚本
```

---

## 一键安装（给智能体的提示词）

复制以下内容发给你的 AI Agent，它会自动完成安装。

> **💡 如果你使用的是 Hermes Agent**，推荐通过 **Memory Provider 插件方式**安装，可获得更好的集成体验（自动同步、进程内调用、工具去重）。详见 [Hermes Memory Provider 适配器安装指南](sinomem-hermes-adapter-guide.md)。

### 方式一：一键脚本（推荐）

```
请帮我安装 SinoMem 记忆系统，执行以下命令：

curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --with-embedding

安装后告诉我结果。
```

### 方式二：从 Gitee 安装（国内更快）

```
请帮我安装 SinoMem 记忆系统，步骤如下：

1. 克隆仓库并安装
   git clone --depth 1 https://gitee.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   pip install -e .

2. 验证安装是否成功
   python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

3. 询问用户是否需要安装嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不安装（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. 安装 embedding 依赖（onnxruntime + sqlite-vec，~200MB）

4. 如果用户选择 B，执行 pip install -e ".[embedding]" 安装依赖。
   然后询问是否需要自动下载 ONNX 模型（约 24MB），如果需要则运行：
   python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

5. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server 方式 — 继续执行以下步骤 6-7

6. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   sinomem:
     args: []
     command: python -m sinomem.entrypoints.mcp_server

7. 设置 SINOMEM_HOME 环境变量，追加到 ~/.bashrc 或 ~/.zshrc：
   export SINOMEM_HOME="$HOME/.local/share/sinomem"

完成后告诉我安装结果。
```

### 方式三：从 GitHub 安装

```
请帮我安装 SinoMem 记忆系统，步骤如下：

1. 克隆仓库并安装
   git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   pip install -e .

2. 验证安装是否成功
   python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

3. 询问用户是否需要安装嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不安装（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. 安装 embedding 依赖（onnxruntime + sqlite-vec，~200MB）

4. 如果用户选择 B，执行 pip install -e ".[embedding]" 安装依赖。
   然后询问是否需要自动下载 ONNX 模型（约 24MB），如果需要则运行：
   python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

5. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server 方式 — 继续执行以下步骤 6-7

6. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   sinomem:
     args: []
     command: python -m sinomem.entrypoints.mcp_server

7. 设置 SINOMEM_HOME 环境变量，追加到 ~/.bashrc 或 ~/.zshrc：
   export SINOMEM_HOME="$HOME/.local/share/sinomem"

完成后告诉我安装结果。
```

---

## 多 Agent 自动记忆同步（插件系统）

除了 MCP Server 的主动调用模式，SinoMem 还提供了**自动同步插件**——Agent 无需显式调用记忆工具即可自动管理长期记忆。

### Claude Code（一键安装）

```bash
bash installers/install_claude_code.sh
```

安装后自动启用三条钩子：对话前检索记忆注入 prompt、写入文件时捕获记忆、会话结束时持久化。

### LangChain（一行接入）

```python
from sinomem.plugins.langchain import AMLMemory

agent = create_react_agent(llm, tools, memory=AMLMemory())
```

### CrewAI（一行接入）

```python
from sinomem.plugins.crewai import AMLCrewMemory

crew = Crew(agents=[...], tasks=[...], memory=AMLCrewMemory())
```

### AutoGen（一行接入）

```python
from sinomem.plugins.autogen import AMLAutoGenMemory

assistant = AssistantAgent(name="agent", memory_provider=AMLAutoGenMemory())
```

### 通用 Python API

```python
from sinomem.plugins import create_plugin

plugin = create_plugin()
plugin.auto_store("用户喜欢飞书")
results = plugin.auto_search("协作工具")
```

---

## 手动安装

```bash
# 国内用户（Gitee）
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash

# GitHub 用户
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# 含语义搜索的完整安装
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --with-embedding
```

> 如需手动安装，可克隆仓库后执行 `pip install -e .`。仓库默认安装到 `~/.local/share/sinomem/`。

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
  sinomem:
    args: []
    command: python -m sinomem.entrypoints.mcp_server
```

重启 Hermes 后生效。

---

## 使用方法

### CLI 命令行

```bash
# 存储记忆
sinomem store "用户偏好飞书发送文件" -c user_pref -t "飞书"

# 关键词搜索
sinomem search "飞书"

# 语义搜索（需安装 embedding 依赖和模型）
sinomem search "怎么给用户传东西" -m semantic

# 混合搜索（推荐）
sinomem search "MCP协议" -m hybrid

# 查看统计
sinomem stats

# 列出所有记忆
sinomem list

# 回收已删除的磁盘空间
sinomem vacuum
```

### MCP Server（Agent 自动调用）

配置完成后，Agent 可以直接调用以下 12 个工具：

| 工具名 | 说明 |
|--------|------|
| `store_memory` | 存储一条记忆（支持去重、TTL 过期、重要性评分） |
| `search_memory` | 搜索记忆（keyword/semantic/hybrid） |
| `get_memory` | 获取指定记忆 |
| `update_memory` | 更新记忆 |
| `delete_memory` | 删除记忆 |
| `delete_memories_by_category` | 按分类批量删除 |
| `list_memories` | 列出记忆（排除过期） |
| `memory_stats` | 查看统计（含过期记忆数） |
| `reindex_memories` | 重建 FTS5 分词索引 |
| `cleanup_memories` | 清理过期记忆 |
| `store_memories_batch` | 批量存储记忆 |
| `search_memories_batch` | 批量搜索多个查询 |

### 数据迁移

```bash
# 从 holographic memory 导入
sinomem import

# 预览（不实际写入）
sinomem import --dry-run

# 为已有记忆生成向量嵌入
sinomem migrate
```

### 数据库维护

```bash
# 回收已删除记忆占用的磁盘空间
sinomem vacuum
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

[Apache 2.0](LICENSE)

Copyright © 2026 [P1M0U](https://github.com/P1M0U)

---

## 联系作者

- 电子邮箱：[p1m0u@foxmail.com](mailto:p1m0u@foxmail.com)
- GitHub：[https://github.com/P1M0U/SinoMem](https://github.com/P1M0U/SinoMem)
- Gitee：[https://gitee.com/P1M0U/SinoMem](https://gitee.com/P1M0U/SinoMem)
