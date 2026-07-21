# SinoMem

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
# Install via one-liner (installs to ~/.local/share/sinomem/)
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# Open a new terminal, then:
sinomem store "User prefers Docker for deployment" -c user_pref
sinomem search "Docker"
# Output: #1  user_pref  score=0.2
#         User prefers Docker for deployment
```

## Who Is This For?

- 🤖 Developers using AI coding assistants like Claude Code, Cursor, Cline, or Hermes
- 🇨🇳 Applications that need high-quality Chinese tokenization (jieba-powered)
- 🔒 Teams with data compliance requirements (100% local SQLite storage)
- 💰 Teams that don't want to pay per-token embedding API costs (local ONNX inference)
- 🔗 Sharing the same long-term memory across multiple AI tools

## Why SinoMem?

| Feature | SinoMem | Mem0 | Built-in Memory |
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
sinomem/        # Core memory engine
├── core/                 # Storage, search, tokenization, embeddings
├── dicts/                # Custom jieba dictionaries
├── entrypoints/          # CLI and MCP Server
├── plugins/              # Multi-agent auto-sync plugins
│   ├── base.py           # Plugin base class
│   ├── claude_code/      # Claude Code hook plugin
│   ├── langchain/        # LangChain BaseMemory component
│   ├── crewai/           # CrewAI Memory component (WIP)
│   ├── autogen/          # AutoGen memory_provider (WIP)
│   └── hermes/           # Hermes MemoryProvider core
│       └── provider.py   # on_memory_write auto-sync
└── tools/                # Data migration tools
hermes_plugin/            # Hermes plugin entry (plugin.yaml + re-export)
installers/               # Claude Code installer script
tests/                    # Tests
models/embedding/         # ONNX embedding model (auto-download)
install.sh                # One-liner install script
```

---

## One-Click Install (Prompt for AI Agent)

Copy the prompt below and send it to your AI Agent — it will handle the install automatically.

> **💡 If you're using Hermes Agent**, we recommend installing via the **Memory Provider plugin** for a better integration experience (auto sync, in-process calls, tool deduplication). See [Hermes Memory Provider Adapter Guide](sinomem-hermes-adapter-guide.md).

### Option A: One-Liner Script (Recommended)

```
Please install SinoMem for me, run:

curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github --with-embedding

Tell me the result when done.
```

### Option B: Install from GitHub

```
Please install SinoMem for me. Steps:

1. Clone and install
   git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   pip install -e .

2. Verify the installation works
   python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

3. Ask the user whether to install embedding dependencies (for semantic search):
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. Install (onnxruntime + sqlite-vec, ~200MB)

4. If user picked B, run pip install -e ".[embedding]", then ask if they want to auto-download the ONNX model (~24MB):
   python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

5. Ask the user to choose an install method:
   — A. Hermes Memory Provider plugin (recommended) — Run `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server — Continue with step 6

6. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   sinomem:
     args: []
     command: python -m sinomem.entrypoints.mcp_server

7. Set SINOMEM_HOME env var, append to ~/.bashrc or ~/.zshrc:
   export SINOMEM_HOME="$HOME/.local/share/sinomem"

Tell me the result when done.
```

### Option C: Install from Gitee (faster in China)

```
Please install SinoMem for me. Steps:

1. Clone and install
   git clone --depth 1 https://gitee.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   pip install -e .

2. Verify the installation works
   python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

3. Ask the user whether to install embedding dependencies (for semantic search):
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. Install (onnxruntime + sqlite-vec, ~200MB)

4. If user picked B, run pip install -e ".[embedding]", then ask if they want to auto-download the ONNX model (~24MB):
   python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

5. Ask the user to choose an install method:
   — A. Hermes Memory Provider plugin (recommended) — Run `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server — Continue with step 6

6. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   sinomem:
     args: []
     command: python -m sinomem.entrypoints.mcp_server

7. Set SINOMEM_HOME env var, append to ~/.bashrc or ~/.zshrc:
   export SINOMEM_HOME="$HOME/.local/share/sinomem"

Tell me the result when done.
```

---

---

## Multi-Agent Auto Memory Sync (Plugin System)

Beyond MCP's active-call mode, SinoMem provides **auto-sync plugins** — the Agent automatically manages long-term memory without explicitly calling memory tools.

### Claude Code (one-click install)

```bash
bash installers/install_claude_code.sh
```

Installs 3 hooks: inject memory context before prompts, capture writes, and persist at session end.

### LangChain (one-line import)

```python
from sinomem.plugins.langchain import AMLMemory

agent = create_react_agent(llm, tools, memory=AMLMemory())
```

### CrewAI (one-line import)

```python
from sinomem.plugins.crewai import AMLCrewMemory

crew = Crew(agents=[...], tasks=[...], memory=AMLCrewMemory())
```

### AutoGen (one-line import)

```python
from sinomem.plugins.autogen import AMLAutoGenMemory

assistant = AssistantAgent(name="agent", memory_provider=AMLAutoGenMemory())
```

### Generic Python API

```python
from sinomem.plugins import create_plugin

plugin = create_plugin()
plugin.auto_store("User prefers Docker")
results = plugin.auto_search("deployment tools")
```

---

## Manual Install

```bash
# One-liner (recommended)
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# Or clone manually
git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
cd ~/.local/share/sinomem
pip install -e .
```

## Uninstall

A one-liner uninstall script is provided to cleanly remove SinoMem and all related configurations:

```bash
# GitHub
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/uninstall.sh | bash

# Gitee (faster in China)
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/uninstall.sh | bash

# Or run locally (after cloning the repo)
bash uninstall.sh
```

**What gets cleaned up:**

| Step | Item | Details |
|------|------|---------|
| pip package | sinomem | Uninstalls from both system pip and Hermes venv |
| Install directory | `~/.local/share/sinomem/` | Removes all project files |
| Environment variables | SINOMEM_HOME / PATH / HF_ENDPOINT | Removes from `.bashrc` / `.zshrc` / `.profile` |
| Hermes plugin | `~/.hermes/plugins/sinomem` | Removes symlink |
| Memory database | `~/.sinomem/memory.db` | **Interactive prompt** — keep or delete |
| Hermes deps | jieba / tokenizers | Uninstalls from Hermes venv (installed by install.sh) |
| Claude Code hooks | `settings.local.json` | Detects and prompts for cleanup (stale hooks cause errors) |
| jieba cache | `~/.cache/jieba` | Asks before cleaning |

> 💡 Before deleting the database, the script shows memory count and file size, and requires a second confirmation. You can keep the database and reuse it after reinstalling.

## Manual Hermes MCP Config

Add to `~/.hermes/config.yaml` under `mcp_servers:`:

```yaml
  sinomem:
    args: []
    command: python -m sinomem.entrypoints.mcp_server
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
sinomem store "User prefers receiving files via Feishu" -c user_pref -t "feishu"

# Keyword search
sinomem search "feishu"

# Semantic search (requires embedding deps + model)
sinomem search "how to send files to user" -m semantic

# Hybrid search (recommended)
sinomem search "MCP protocol" -m hybrid

# Stats
sinomem stats

# List all memories
sinomem list

# Reclaim disk space after deletes
sinomem vacuum
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
sinomem import

# Preview (dry run)
sinomem import --dry-run

# Generate vector embeddings for existing memories
sinomem migrate
```

### Database Maintenance

```bash
# Reclaim disk space from deleted memories
sinomem vacuum
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
- GitHub: [https://github.com/P1M0U/SinoMem](https://github.com/P1M0U/SinoMem)
- Gitee: [https://gitee.com/P1M0U/SinoMem](https://gitee.com/P1M0U/SinoMem)
