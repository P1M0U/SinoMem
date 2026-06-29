# Agent Memory Lite

English | [中文](README.md)

> v0.5.5

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-CJK-blue)
![ONNX](https://img.shields.io/badge/ONNX-Inference-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-Vector-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-Package--Mgr-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

Lightweight, Chinese-friendly Agent memory system with local semantic search. Built on SQLite + FTS5 + ONNX embeddings — zero API calls.

## Features

- **Chinese FTS5 Search** — jieba tokenization + SQLite FTS5, zero API calls
- **Semantic Search** — Local ONNX embedding model (~113MB), no external services
- **Batch Embedding Inference** — ONNX Runtime batch inference for better performance on large-scale memory imports
- **Hybrid Search** — Keyword + semantic weighted ranking, balancing precision and recall
- **MCP Server** — Standard protocol, 10 tools, works with any MCP-compatible Agent
- **CLI Tool** — 10 subcommands (store / search / get / update / delete / list / stats / vacuum / clean / reindex) for scripting and automation
- **Data Migration** — Import from holographic memory, generate embeddings for existing memories
- **Content Validation** — Auto-truncation of overly long content (8000 chars) to prevent search quality degradation
- **Auto Deduplication** — Skips duplicate content by default, configurable via parameter
- **Database Maintenance** — VACUUM, reindex, batch delete by category

---

## Project Structure

```
agent_memory_lite/
├── __init__.py               # Version
├── core/                     # Core business logic
│   ├── __init__.py
│   ├── config.py             # Centralized config (paths, defaults)
│   ├── engine.py             # Facade class MemoryEngine, composes store + search
│   ├── store.py              # Memory CRUD + VACUUM + dedup + batch delete
│   ├── search.py             # Three-mode search engine (SearchEngine)
│   ├── embedder.py           # ONNX embedding model wrapper + batch inference (Embedder)
│   ├── schema.py             # SQLite schema constants
│   └── tokenizer.py          # jieba Chinese tokenizer
├── entrypoints/              # Public entry points
│   ├── __init__.py
│   ├── cli.py                # CLI command-line tool
│   └── mcp_server.py         # MCP Server entry point (FastMCP)
└── tools/                    # Data migration tools
    ├── __init__.py
    ├── migrate.py            # Vector migration (generate embeddings for existing memories)
    └── import_holographic.py # Import data from holographic memory
tests/
├── test_engine.py            # Engine integration tests
├── test_store.py             # Storage layer unit tests
├── test_search.py            # Search layer unit tests
├── test_mcp_server.py        # MCP Server tests
├── test_migrate.py           # Migration tests
└── test_import_holographic.py  # Import tests
dicts/                        # Custom jieba dictionaries
models/embedding/              # ONNX embedding model (download separately)
```

---

## One-Click Install (Prompt for AI Agent)

Copy the prompt below and send it to your AI Agent — it will handle clone, install, and config automatically:

### Option A: Install from GitHub

```
Please install Agent Memory Lite for me. Steps:

1. Clone the repo to ~/Desktop/Agent-Memory-Lite/
   git clone https://github.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. Enter the project and install dependencies with uv
   cd ~/Desktop/Agent-Memory-Lite
   uv sync

3. Verify the installation works
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

6. Make the wrapper executable
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

Tell me when done.
```

### Option B: Install from Gitee (faster in China)

```
Please install Agent Memory Lite for me. Steps:

1. Clone the repo to ~/Desktop/Agent-Memory-Lite/
   git clone https://gitee.com/pimou/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. Enter the project and install dependencies with uv
   cd ~/Desktop/Agent-Memory-Lite
   uv sync

3. Verify the installation works
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

6. Make the wrapper executable
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

Tell me when done.
```

---

## Manual Install

```bash
# 1. Clone
git clone https://github.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite
cd ~/Desktop/Agent-Memory-Lite

# 2. Install dependencies
uv sync

# 3. Verify
uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"
```

## Manual Hermes MCP Config

Add to `~/.hermes/config.yaml` under `mcp_servers:`:

```yaml
  agent-memory-lite:
    args: []
    command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

Create the wrapper script:

```bash
cat > ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh << 'EOF'
#!/bin/bash
cd ~/Desktop/Agent-Memory-Lite
exec uv run python -m agent_memory_lite.entrypoints.mcp_server
EOF
chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

Restart Hermes to activate.

## Download Embedding Model (Optional, for Semantic Search)

The embedding model is ~113MB and needs to be downloaded separately:

```bash
# Create model directory
mkdir -p models/embedding/onnx

# Download model files (choose one)

# Option A: From HuggingFace
pip install huggingface-hub
python -c "from huggingface_hub import hf_hub_download; hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding'); hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')"

# Option B: From hf-mirror.com (faster in China)
HF_ENDPOINT=https://hf-mirror.com python -c "from huggingface_hub import hf_hub_download; hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding'); hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')"
```

Without the model, semantic search degrades gracefully to keyword search.

---

## Usage

### CLI

```bash
# Store a memory
uv run python -m agent_memory_lite.entrypoints.cli store "User prefers receiving files via Feishu" -c user_pref -t "feishu"

# Keyword search
uv run python -m agent_memory_lite.entrypoints.cli search "feishu"

# Semantic search
uv run python -m agent_memory_lite.entrypoints.cli search "how to send files to user" -m semantic

# Hybrid search
uv run python -m agent_memory_lite.entrypoints.cli search "MCP protocol" -m hybrid

# Stats
uv run python -m agent_memory_lite.entrypoints.cli stats

# List all memories
uv run python -m agent_memory_lite.entrypoints.cli list

# Reclaim disk space after deletes
uv run python -m agent_memory_lite.entrypoints.cli vacuum
```

### MCP Server (Agent auto-calls)

Once configured, the Agent can call these 9 tools directly:

| Tool | Description |
|------|-------------|
| `store_memory` | Store a memory (with dedup) |
| `search_memory` | Search memories (keyword/semantic/hybrid) |
| `get_memory` | Get a specific memory |
| `update_memory` | Update a memory |
| `delete_memory` | Delete a memory |
| `delete_memories_by_category` | Batch delete by category |
| `list_memories` | List memories |
| `memory_stats` | View statistics |
| `reindex_memories` | Rebuild FTS5 token index |

### Data Migration

```bash
# Import from holographic memory
uv run python -m agent_memory_lite.entrypoints.cli import

# Preview (dry run)
uv run python -m agent_memory_lite.entrypoints.cli import --dry-run

# Generate vector embeddings for existing memories
uv run python -m agent_memory_lite.entrypoints.cli migrate
```

### Database Maintenance

```bash
# Reclaim disk space from deleted memories
uv run python -m agent_memory_lite.entrypoints.cli vacuum
```

After heavy deletions, SQLite does not automatically reclaim disk space. The `vacuum` command rebuilds the database file to free space.

---

## Search Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| `keyword` | FTS5 keyword matching | Precise lookup, e.g. searching "feishu" |
| `semantic` | Vector semantic similarity | Fuzzy lookup, e.g. searching "how to send files" |
| `hybrid` | Keyword + semantic weighted | General purpose, balances precision and recall |

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
```

## License

MIT
