# Agent Memory Lite

English | [中文](README.md)

> v0.5.0

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
- **Hybrid Search** — Keyword + semantic weighted ranking
- **MCP Server** — Standard protocol, works with any MCP-compatible Agent
- **CLI Tool** — Command-line interface for scripting and automation
- **Data Migration** — Import from holographic memory

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
   uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"

4. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.mcp_server

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
   uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"

4. Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   agent-memory-lite:
     args: []
     command: /home/pimou/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh

5. Create wrapper script ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh with content:
   #!/bin/bash
   cd ~/Desktop/Agent-Memory-Lite
   exec uv run python -m agent_memory_lite.mcp_server

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
uv run python -c "from agent_memory_lite.engine import MemoryEngine; print('ok')"
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
exec uv run python -m agent_memory_lite.mcp_server
EOF
chmod +x ~/.hermes/scripts/agent-memory-lite-mcp-wrapper.sh
```

Restart Hermes to activate.

---

## Usage

### CLI

```bash
# Store a memory
uv run python -m agent_memory_lite.cli store "User prefers receiving files via Feishu" -c user_pref -t "feishu"

# Keyword search
uv run python -m agent_memory_lite.cli search "feishu"

# Semantic search
uv run python -m agent_memory_lite.cli search "how to send files to user" -m semantic

# Hybrid search
uv run python -m agent_memory_lite.cli search "MCP protocol" -m hybrid

# Stats
uv run python -m agent_memory_lite.cli stats

# List all memories
uv run python -m agent_memory_lite.cli list
```

### MCP Server (Agent auto-calls)

Once configured, the Agent can call these 7 tools directly:

| Tool | Description |
|------|-------------|
| `store_memory` | Store a memory |
| `search_memory` | Search memories (keyword/semantic/hybrid) |
| `get_memory` | Get a specific memory |
| `update_memory` | Update a memory |
| `delete_memory` | Delete a memory |
| `list_memories` | List memories |
| `memory_stats` | View statistics |

### Data Migration

```bash
# Import from holographic memory
uv run python -m agent_memory_lite.cli import

# Preview (dry run)
uv run python -m agent_memory_lite.cli import --dry-run

# Generate vector embeddings for existing memories
uv run python -m agent_memory_lite.cli migrate
```

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
