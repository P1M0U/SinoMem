# Agent Memory Lite

[English](README_EN.md) | 中文

轻量级中文友好的 Agent 记忆增强系统。基于 SQLite + FTS5 + 本地向量搜索，零 API 调用。

## 特性

- **中文 FTS5 搜索** — jieba 分词 + SQLite FTS5，零 API 调用
- **语义搜索** — 本地 ONNX 嵌入模型（~113MB），不依赖外部服务
- **混合搜索** — 关键词 + 语义加权排序
- **MCP Server** — 标准协议，可接入任何支持 MCP 的 Agent
- **CLI 工具** — 命令行操作，方便脚本集成
- **数据迁移** — 支持从 holographic memory 导入

## 快速开始

```bash
# 安装依赖
uv sync

# 存储记忆
uv run python -m agent_memory_lite.cli store "用户偏好飞书发送文件" -c user_pref -t "飞书"

# 关键词搜索
uv run python -m agent_memory_lite.cli search "飞书"

# 语义搜索
uv run python -m agent_memory_lite.cli search "怎么给用户传东西" -m semantic

# 混合搜索
uv run python -m agent_memory_lite.cli search "MCP协议" -m hybrid

# 统计
uv run python -m agent_memory_lite.cli stats
```

## 作为 MCP Server 使用

```bash
# 直接启动
uv run python -m agent_memory_lite.mcp_server

# 或通过 wrapper 脚本
~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

在 Hermes `config.yaml` 中添加：

```yaml
mcp_servers:
  agent-memory-lite:
    args: []
    command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

## 数据迁移

```bash
# 从 holographic memory 导入
uv run python -m agent_memory_lite.cli import

# 预览（不实际写入）
uv run python -m agent_memory_lite.cli import --dry-run

# 为已有记忆生成向量
uv run python -m agent_memory_lite.cli migrate
```

## 搜索模式

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| `keyword` | FTS5 关键词匹配 | 精确查找，如搜"飞书" |
| `semantic` | 向量语义相似度 | 模糊查找，如搜"怎么传文件" |
| `hybrid` | 关键词 + 语义加权 | 通用场景，兼顾精确和模糊 |

## 项目结构

```
Agent-Memory-Lite/
├── pyproject.toml                  # 项目配置
├── README.md
├── README_EN.md
├── LICENSE
├── dicts/
│   └── tech_terms.txt              # jieba 自定义词典
├── models/
│   └── embedding/                  # ONNX 嵌入模型（~113MB）
│       ├── onnx/
│       │   └── model_quantized.onnx
│       ├── tokenizer.json
│       └── config.json
├── agent_memory_lite/
│   ├── __init__.py
│   ├── engine.py                   # 核心引擎（FTS5 + 向量）
│   ├── tokenizer.py                # jieba 分词封装
│   ├── embedder.py                 # ONNX 嵌入模型
│   ├── mcp_server.py               # MCP Server
│   ├── cli.py                      # CLI 工具
│   ├── migrate.py                  # 向量迁移
│   └── import_holographic.py       # holographic 数据导入
└── tests/
    └── test_engine.py
```

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
测试：pytest
```

## 测试

```bash
uv run pytest tests/ -v
```

## License

MIT
