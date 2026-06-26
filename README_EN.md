# Agent Memory Lite

English | [中文](README.md)

Lightweight, Chinese-friendly Agent memory system with local semantic search. Built on SQLite + FTS5 + ONNX embeddings — zero API calls.

## Features

- **Chinese FTS5 Search** — jieba tokenization + SQLite FTS5, zero API calls
- **Semantic Search** — Local ONNX embedding model (~113MB), no external services
- **Hybrid Search** — Keyword + semantic weighted ranking
- **MCP Server** — Standard protocol, works with any MCP-compatible Agent
- **CLI Tool** — Command-line interface for scripting and automation
- **Data Migration** — Import from holographic memory

## Quick Start

```bash
# Install dependencies
uv sync

# Store a memory
uv run python -m agent_memory_lite.cli store "User prefers receiving files via Feishu" -c user_pref -t "feishu"

# Keyword search
uv run python -m agent_memory_lite.cli search "feishu"

# Semantic search
uv run python -m agent_memory_lite.cli search "how to send files to user" -m semantic

# Hybrid search
uv run python -m agent_memory_lite.cli search "MCP protocol" -m hybrid

# Statistics
uv run python -m agent_memory_lite.cli stats
```

## As MCP Server

```bash
# Start directly
uv run python -m agent_memory_lite.mcp_server

# Or via wrapper script
~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

Add to Hermes `config.yaml`:

```yaml
mcp_servers:
  agent-memory-lite:
    args: []
    command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

## Data Migration

```bash
# Import from holographic memory
uv run python -m agent_memory_lite.cli import

# Preview (dry run)
uv run python -m agent_memory_lite.cli import --dry-run

# Generate vectors for existing memories
uv run python -m agent_memory_lite.cli migrate
```

## Search Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `keyword` | FTS5 keyword matching | Precise lookup, e.g. searching "feishu" |
| `semantic` | Vector semantic similarity | Fuzzy lookup, e.g. searching "how to send files" |
| `hybrid` | Keyword + semantic weighted | General purpose, balances precision and recall |

## Project Structure

```
Agent-Memory-Lite/
├── pyproject.toml                  # Project config
├── README.md
├── README_EN.md
├── LICENSE
├── dicts/
│   └── tech_terms.txt              # jieba custom dictionary
├── models/
│   └── embedding/                  # ONNX embedding model (~113MB)
│       ├── onnx/
│       │   └── model_quantized.onnx
│       ├── tokenizer.json
│       └── config.json
├── agent_memory_lite/
│   ├── __init__.py
│   ├── engine.py                   # Core engine (FTS5 + vectors)
│   ├── tokenizer.py                # jieba tokenization wrapper
│   ├── embedder.py                 # ONNX embedding model
│   ├── mcp_server.py               # MCP Server
│   ├── cli.py                      # CLI tool
│   ├── migrate.py                  # Vector migration
│   └── import_holographic.py       # holographic data import
└── tests/
    └── test_engine.py
```

## Tech Stack

```
Language:      Python 3.11+
Package Mgr:   uv
MCP Protocol:  fastmcp 3.x
Storage:       SQLite + FTS5
CJK Tokenizer: jieba + custom dictionary
Vector Search: sqlite-vec
Embeddings:    ONNX quantized (paraphrase-multilingual-MiniLM-L12-v2)
CLI:           click
Testing:       pytest
```

## Testing

```bash
uv run pytest tests/ -v
```

## License

MIT
