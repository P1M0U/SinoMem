# Agent Memory Lite

English | [中文](README.md)

> v0.6.7

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white)
![jieba](https://img.shields.io/badge/jieba-CJK-blue)
![ONNX](https://img.shields.io/badge/ONNX-Inference-FF6F00?logo=onnx&logoColor=white)
![sqlite-vec](https://img.shields.io/badge/sqlite--vec-Vector-purple)
![MCP](https://img.shields.io/badge/MCP-Server-green)
![uv](https://img.shields.io/badge/uv-Package--Mgr-orange)
![License](https://img.shields.io/badge/License-Apache%202.0-blue)

> Give your AI Agent a long-term memory that never forgets.
> One command to connect, zero API cost, 100% local storage.

Lightweight, Chinese-friendly Agent memory system with local semantic search — SQLite + FTS5 + jieba tokenization + ONNX embeddings, zero API calls. Connects to Claude Code, Cursor, Cline, Hermes, and any MCP-compatible Agent.

## Quick Start (30 seconds)

```bash
git clone https://github.com/P1M0U/Agent-Memory-Lite.git && cd Agent-Memory-Lite
uv sync

# Store a memory, then search it
uv run aml store "User prefers Docker for deployment" -c user_pref
uv run aml search "Docker"
# Output: #1  user_pref
#         User prefers Docker for deployment
```

## Who Is This For?

- 🤖 Developers using AI coding assistants like Claude Code, Cursor, Cline, or Hermes
- 🇨🇳 Applications that need high-quality Chinese tokenization (jieba-powered)
- 🔒 Teams with data compliance requirements (100% local SQLite storage)
- 💰 Teams that don't want to pay per-token embedding API costs (local ONNX inference)
- 🔗 Sharing the same long-term memory across multiple AI tools

## Why Agent Memory Lite?

| Feature | Agent Memory Lite | Mem0 | Built-in Memory |
|---------|-------------------|------|----------------|
| Chinese Tokenization | ✅ jieba custom | Default | Default |
| Local Deployment | ✅ SQLite single file | ❌ API required | ✅ Framework-locked |
| Embedding Model | ✅ ONNX local ~24MB | OpenAI API | None |
| MCP Protocol | ✅ Standard MCP Server | ❌ | ❌ |
| Cross-Agent Sharing | ✅ One .db file | ❌ | ❌ |
| Database Backup | ✅ Copy one file | ❌ | ❌ |
| Cost | 💰 Zero API fees | 💰💸 Per-token billing | 💰 Zero |

## Features

- **Chinese FTS5 Search** — jieba tokenization + SQLite FTS5, same tokenizer for write and query, token-aligned
- **Semantic Search** — Local ONNX embedding model (~24MB min), optional install, dual-mode auto-detection
- **Hybrid Search** — Keyword + semantic weighted ranking, balancing precision and recall
- **MCP Server** — Standard protocol, 12 tools, works with any MCP-compatible Agent
- **Multi-Agent Auto-Sync Plugins** — Claude Code / LangChain / CrewAI / AutoGen / Hermes, all supported
- **CLI Tool** — 15 subcommands (store / search / get / update / delete / list / stats / vacuum / clean / reindex / cleanup / migrate / import / store-batch / search-batch)
- **Data Migration** — Import from holographic memory, generate embeddings for existing memories
- **Auto Deduplication** — Skips duplicate content by default
- **Database Maintenance** — VACUUM, reindex, batch delete by category
- **Content Validation** — Auto-truncation of overly long content (8000 chars)
- **Thread-safe** — check_same_thread=False for multi-agent concurrent access

---

## Project Structure

```
agent_memory_lite/        # Core memory engine
├── core/                 # Storage, search, tokenization, embeddings
├── entrypoints/          # CLI and MCP Server
├── plugins/              # Multi-agent auto-sync plugins
│   ├── base.py           # Plugin base class
│   ├── claude_code/      # Claude Code hook plugin
│   ├── langchain/        # LangChain BaseMemory component
│   ├── crewai/           # CrewAI Memory component
│   ├── autogen/          # AutoGen memory_provider
│   └── hermes/           # Hermes MemoryProvider core
│       └── provider.py   # on_memory_write auto-sync
└── tools/                # Data migration tools
hermes_plugin/            # Hermes plugin entry (plugin.yaml + re-export)
installers/               # One-click install scripts
tests/                    # Tests
dicts/                    # Custom jieba dictionaries
models/embedding/         # ONNX embedding model (download separately)
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

4. Ask the user whether to download an embedding model (for semantic search), present these options:
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. paraphrase-multilingual-MiniLM-L12-v2 (~113MB, 384-dim, 50+ languages, best for mixed-language content)
   — C. bge-small-zh-v1.5 (~24MB, 512-dim, Chinese-optimized, best for primarily Chinese, much smaller)
   If user picks B or C, download the corresponding model from hf-mirror.com mirror to models/embedding/

5. Ask the user to choose an install method, present these options:
   — A. Hermes Memory Provider plugin (recommended) — Run `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`, then follow the [Adapter Guide](agent-memory-lite-hermes-adapter-guide.md) for the remaining steps (skip steps 6–8)
   — B. MCP Server — Continue with steps 6–8 below

6. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers (replace /home/your-username with your actual home path):
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
   git clone https://gitee.com/P1M0U/Agent-Memory-Lite.git ~/Desktop/Agent-Memory-Lite

2. Enter the project and install dependencies with uv (use Tsinghua mirror for speed in China)
   cd ~/Desktop/Agent-Memory-Lite
   uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

3. Verify the installation works
   uv run python -c "from agent_memory_lite.core.engine import MemoryEngine; print('ok')"

4. Ask the user whether to download an embedding model (for semantic search), present these options:
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. paraphrase-multilingual-MiniLM-L12-v2 (~113MB, 384-dim, 50+ languages, best for mixed-language content)
   — C. bge-small-zh-v1.5 (~24MB, 512-dim, Chinese-optimized, best for primarily Chinese, much smaller)
   If user picks B or C, download the corresponding model from hf-mirror.com mirror to models/embedding/

5. Ask the user to choose an install method, present these options:
   — A. Hermes Memory Provider plugin (recommended) — Run `cp -r ~/Desktop/Agent-Memory-Lite/hermes_plugin/ ~/.hermes/plugins/agent-memory-lite/`, then follow the [Adapter Guide](agent-memory-lite-hermes-adapter-guide.md) for the remaining steps (skip steps 6–8)
   — B. MCP Server — Continue with steps 6–8 below

6. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers (replace /home/your-username with your actual home path):
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

---

## Multi-Agent Auto Memory Sync (Plugin System)

Beyond MCP's active-call mode, Agent Memory Lite provides **auto-sync plugins** — the Agent automatically manages long-term memory without explicitly calling memory tools.

### Claude Code (one-click install)

```bash
bash installers/install_claude_code.sh
```

Installs 3 hooks: inject memory context before prompts, capture writes, and persist at session end.

### LangChain (one-line import)

```python
from agent_memory_lite.plugins.langchain import AMLMemory

agent = create_react_agent(llm, tools, memory=AMLMemory())
```

### CrewAI (one-line import)

```python
from agent_memory_lite.plugins.crewai import AMLCrewMemory

crew = Crew(agents=[...], tasks=[...], memory=AMLCrewMemory())
```

### AutoGen (one-line import)

```python
from agent_memory_lite.plugins.autogen import AMLAutoGenMemory

assistant = AssistantAgent(name="agent", memory_provider=AMLAutoGenMemory())
```

### Generic Python API

```python
from agent_memory_lite.plugins import create_plugin

plugin = create_plugin()
plugin.auto_store("User prefers Docker")
results = plugin.auto_search("deployment tools")
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

Once configured, the Agent can call these 12 tools directly:

| Tool | Description |
|------|-------------|
| `store_memory` | Store a memory (dedup, TTL expiry, importance) |
| `search_memory` | Search memories (keyword/semantic/hybrid) |
| `get_memory` | Get a specific memory |
| `update_memory` | Update a memory |
| `delete_memory` | Delete a memory |
| `delete_memories_by_category` | Batch delete by category |
| `list_memories` | List memories (exclude expired) |
| `memory_stats` | View statistics (including expired count) |
| `reindex_memories` | Rebuild FTS5 token index |
| `cleanup_memories` | Clean up expired memories |
| `store_memories_batch` | Batch store memories |
| `search_memories_batch` | Batch search multiple queries |

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

[Apache 2.0](LICENSE)

Copyright © 2026 [P1M0U](https://github.com/P1M0U)

---

## Contact

- Email: [p1m0u@foxmail.com](mailto:p1m0u@foxmail.com)
- GitHub: [https://github.com/P1M0U/Agent-Memory-Lite](https://github.com/P1M0U/Agent-Memory-Lite)
- Gitee: [https://gitee.com/P1M0U/Agent-Memory-Lite](https://gitee.com/P1M0U/Agent-Memory-Lite)
