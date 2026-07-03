# Agent Memory Lite

English | [中文](README.md)

> v0.6.0

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-CJK-blue)
![ONNX](https://img.shields.io/badge/ONNX-Inference-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-Vector-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-Package--Mgr-orange)
![License](https://img.shields.io/badge/License-AGPLv3-blue)

Lightweight, Chinese-friendly Agent memory system with local semantic search. Built on SQLite + FTS5 + jieba tokenization + ONNX embeddings — zero API calls.

## Why This Exists

### Agent Built-in Memory vs. Agent Memory Lite

Agent frameworks (e.g., Claude Code) ship with session-scoped memory that handles **in-session context**. This project addresses a different layer:

| Dimension | Agent Built-in Memory | Agent Memory Lite |
|-----------|----------------------|-------------------|
| **Scope** | Session-level context | Cross-session long-term memory |
| **Search** | FTS5 (framework default tokenizer) | FTS5 (jieba custom CJK tokenizer) |
| **Semantic Search** | No | Optional ONNX local semantic search |
| **Auto Dedup** | No | Enabled by default |
| **Batch Delete** | No | By-category + clear-all |
| **Data Independence** | Framework-locked | Standalone `.db`, portable & backup-ready |
| **Multi-Agent Sharing** | N/A | Same memory shared across multiple MCP Agents |

### Cross-Agent Memory Hub

The unique value of this project is **framework-agnostic memory**. One `.db` file can be shared by any MCP-compatible Agent or IDE (Claude Code, Claude Desktop, Cursor, Cline, etc.):

```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Claude   │  │ Cursor   │  │ Cline    │  ... any MCP-compatible Agent
│  Code    │  │          │  │          │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   │ MCP Protocol (stdio)
            ┌──────┴──────┐
            │ Agent Memory │
            │     Lite     │
            └──────┬──────┘
                   │
            ┌──────┴──────┐
            │  memory.db  │  Standalone storage — backup, migrate, analyze
            └─────────────┘
```

What this enables:
- Memories stored via Claude Code remain accessible when switching to Cursor
- User preferences learned in one IDE benefit another
- Memory data survives tool upgrades — independent from any single tool
- One memory store becomes a true "cross-tool long-term knowledge base"

## Features

- **Chinese FTS5 Search** — jieba tokenization + SQLite FTS5, same tokenizer for write and query, token-aligned
- **Semantic Search** — Local ONNX embedding model (~113MB), optional install, no external services
- **Batch Embedding Inference** — ONNX Runtime batch inference for better performance on large-scale memory imports
- **Hybrid Search** — Keyword + semantic weighted ranking, balancing precision and recall
- **MCP Server** — Standard protocol, 10 tools, works with any MCP-compatible Agent
- **CLI Tool** — 10 subcommands (store / search / get / update / delete / list / stats / vacuum / clean / reindex) for scripting and automation
- **Data Migration** — Import from holographic memory, generate embeddings for existing memories
- **Content Validation** — Auto-truncation of overly long content (8000 chars) to prevent search quality degradation
- **Auto Deduplication** — Skips duplicate content by default, configurable via parameter
- **Database Maintenance** — VACUUM, reindex, batch delete by category
- **Thread-safe** — check_same_thread=False for multi-agent concurrent access

---

## Project Structure

```
agent_memory_lite/
├── core/           # Core business logic (storage, search, tokenization, embeddings)
├── entrypoints/    # Public entry points (CLI and MCP Server)
└── tools/          # Data migration tools
tests/              # Tests
dicts/              # Custom jieba dictionaries
hermes_plugin/      # Hermes Memory Provider adapter plugin
models/embedding/   # ONNX embedding model (download separately)
```

---

## One-Click Install (Prompt for AI Agent)

Copy the prompt below and send it to your AI Agent — it will handle clone, install, and config automatically.

> **💡 If you're using Hermes Agent**, we recommend installing via the **Memory Provider plugin** for a better integration experience (auto sync, in-process calls, tool deduplication). See [Hermes Memory Provider Adapter Guide](agent-memory-lite-hermes-adapter-guide.md).

### Option A: Install from GitHub

```
Please install Agent Memory Lite for me. Steps:

1. Clone the repo to ~/Desktop/Agent-Memory-Lite/
   git clone https://github.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. Enter the project and install dependencies with uv (use Tsinghua mirror for speed in China)
   cd ~/Desktop/Agent-Memory-Lite
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

3. Verify the installation works
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. Ask the user whether to download an embedding model (for semantic search), choose one:
   — **paraphrase-multilingual-MiniLM-L12-v2** (~113MB, 384-dim, 50+ languages, best for mixed-language content)
   — **bge-small-zh-v1.5** (~24MB, 512-dim, Chinese-optimized, best for primarily Chinese, much smaller)
   — See the "Download Embedding Model" section in the project README for download commands (use hf-mirror.com mirror for speed in China)
   — If the user chooses not to download, skip this step; semantic search degrades gracefully to keyword search

5. Ask the user to choose an install method:
   — **Hermes Memory Provider plugin (recommended)**: Run `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`, then follow the [Adapter Guide](agent-memory-lite-hermes-adapter-guide.md) for the remaining steps
   — **MCP Server**: Continue with steps 6–8 below

6. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers (replace /home/your-username with your actual home path):
   agent-memory-lite:
     args: []
     command: /home/your-username/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

7. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

8. Make the wrapper executable
   chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

Tell me when done.
```

### Option B: Install from Gitee (faster in China)

```
Please install Agent Memory Lite for me. Steps:

1. Clone the repo to ~/Desktop/Agent-Memory-Lite/
   git clone https://gitee.com/pimou/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. Enter the project and install dependencies with uv (use Tsinghua mirror for speed in China)
   cd ~/Desktop/Agent-Memory-Lite
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

3. Verify the installation works
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. Ask the user whether to download an embedding model (for semantic search), choose one:
   — **paraphrase-multilingual-MiniLM-L12-v2** (~113MB, 384-dim, 50+ languages, best for mixed-language content)
   — **bge-small-zh-v1.5** (~24MB, 512-dim, Chinese-optimized, best for primarily Chinese, much smaller)
   — See the "Download Embedding Model" section in the project README for download commands (use hf-mirror.com mirror for speed in China)
   — If the user chooses not to download, skip this step; semantic search degrades gracefully to keyword search

5. Ask the user to choose an install method:
   — **Hermes Memory Provider plugin (recommended)**: Run `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`, then follow the [Adapter Guide](agent-memory-lite-hermes-adapter-guide.md) for the remaining steps
   — **MCP Server**: Continue with steps 6–8 below

6. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers (replace /home/your-username with your actual home path):
   agent-memory-lite:
     args: []
     command: /home/your-username/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

7. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.entrypoints.mcp_server

8. Make the wrapper executable
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
    command: /home/your-username/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```
(Replace `/home/your-username` with your actual home path)

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

Two embedding models are supported — choose one based on your use case (the system auto-detects model type):

| Model | Size | Dim | Language | Best For |
|-------|------|-----|----------|----------|
| **paraphrase-multilingual-MiniLM-L12-v2** | ~113MB | 384 | 50+ languages | Mixed-language content, Chinese + English |
| **bge-small-zh-v1.5** | ~24MB | 512 | Chinese-optimized | Primarily Chinese, smaller size, better Chinese accuracy |

```bash
# Create model directory
mkdir -p models/embedding/onnx

# Install download tool
pip install huggingface-hub

# ─── Option A: paraphrase-multilingual-MiniLM-L12-v2 (multilingual, ~113MB) ───
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'onnx/model_quantized.onnx', local_dir='models/embedding')
hf_hub_download('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2', 'tokenizer.json', local_dir='models/embedding')
"

# ─── Option B: bge-small-zh-v1.5 (Chinese-optimized, ~24MB) ───
python -c "
from huggingface_hub import hf_hub_download
hf_hub_download('Xenova/bge-small-zh-v1.5', 'onnx/model_quantized.onnx', local_dir='models/embedding')
hf_hub_download('Xenova/bge-small-zh-v1.5', 'tokenizer.json', local_dir='models/embedding')
"
```

> **💡 Users in China**: Set `HF_ENDPOINT=https://hf-mirror.com` before downloading for faster access.

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

## License

[AGPLv3](LICENSE)

Copyright © 2026 [P1M0U](https://github.com/P1M0U)

---

## Contact

- Email: [p1m0u@foxmail.com](mailto:p1m0u@foxmail.com)
- GitHub: [https://github.com/P1M0U/Agent-Memory-Lite](https://github.com/P1M0U/Agent-Memory-Lite)
- Gitee: [https://gitee.com/pimou/Agent-Memory-Lite](https://gitee.com/pimou/Agent-Memory-Lite)
