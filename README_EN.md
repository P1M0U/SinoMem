# SinoMem

English | [中文](README.md)

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.7.2-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/SQLite-FTS5-003B57?logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/jieba-CJK-blue" alt="jieba">
  <img src="https://img.shields.io/badge/ONNX-Inference-FF6F00?logo=onnx&logoColor=white" alt="ONNX">
  <img src="https://img.shields.io/badge/sqlite--vec-Vector-purple" alt="sqlite-vec">
  <img src="https://img.shields.io/badge/MCP-Server-green" alt="MCP">
  <img src="https://img.shields.io/badge/uv-Package--Mgr-orange" alt="uv">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue" alt="License">
</p>

> Give your AI Agent a long-term memory that never forgets.
> One command to connect, zero API cost, 100% local storage.

Lightweight, Chinese-friendly Agent memory system with local semantic search — SQLite + FTS5 + jieba tokenization + ONNX embeddings, zero API calls. Connects to Claude Code, Cursor, Cline, Hermes, and any MCP-compatible Agent.

> 🎯 A local long-term memory component built for AI Agents, compatible with the standard MCP protocol.

⭐ If SinoMem helps you, a Star would be greatly appreciated — it helps more developers discover the project!

## 📑 Table of Contents

- [Preview](#-preview)
- [Quick Start (30 seconds)](#quick-start-30-seconds)
- [Who Is This For?](#who-is-this-for)
- [Why SinoMem?](#why-sinomem)
- [Core Features](#core-features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Download Embedding Model (Optional, for Semantic Search)](#download-embedding-model-optional-for-semantic-search)
- [Manual Hermes MCP Config](#manual-hermes-mcp-config)
- [Multi-Agent Auto Memory Sync (Plugin System)](#multi-agent-auto-memory-sync-plugin-system)
- [Usage](#usage)
- [Search Modes](#search-modes)
- [Uninstall](#uninstall)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🖼 Preview

### System Architecture

![SinoMem System Architecture](assets/SinoMem系统架构简图.png)

### Demo Video / GIF (Coming Soon)

> **📌 Demo GIF path: `assets/demo.gif` (shows store / search operations).**

*(Demo assets are on the way — feel free to contribute a demo GIF via PR.)*

---

## Quick Start (30 seconds)

```bash
# China / Asia users (Gitee, recommended)
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash

# International users (GitHub)
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# Open a new terminal, then:
sinomem store "User prefers Docker for deployment" -c user_pref
sinomem search "Docker"
# Output: #1  user_pref  score=0.2
#         User prefers Docker for deployment
```

> ⚠️ **You must open a new terminal window** (or run `source ~/.bashrc`) after install — otherwise the `sinomem` command won't be recognized.
>
> 💾 The default memory database lives at `~/.sinomem/memory.db` — to back it up, simply copy this single file.

---

## Who Is This For?

- 🤖 Developers using AI coding assistants like Claude Code, Cursor, Cline, or Hermes
- 🇨🇳 Applications that need high-quality Chinese tokenization (jieba-powered)
- 🔒 Teams with data compliance requirements (100% local SQLite storage)
- 💰 Teams that don't want to pay per-token embedding API costs (local ONNX inference)
- 🔗 Sharing the same long-term memory across multiple AI tools

---

## Why SinoMem?

| Feature | SinoMem | Mem0 | Built-in Memory |
|---------|-------------------|------|----------------|
| Chinese Tokenization | ✅ jieba custom | Default | Default |
| Local Deployment | ✅ SQLite single file | ❌ API required | ✅ Framework-locked |
| Embedding Model | ✅ ONNX local ~24MB | OpenAI API | None |
| MCP Protocol | ✅ Standard MCP Server | ❌ | ❌ |
| Cross-Agent Sharing | ✅ One .db file | ❌ | ❌ (Agent-bound, can't share across tools) |
| Database Backup | ✅ Copy one file | ❌ | ❌ |
| Cost | 💰 Zero API fees | 💰💸 Per-token billing | 💰 Zero |

---

## Core Features

- **Chinese FTS5 Search** — jieba tokenization + SQLite FTS5, same tokenizer for write and query, token-aligned
- **Semantic Search** — Local ONNX embedding model (~24MB min), optional install, dual-mode auto-detection
- **Hybrid Search** — RRF (Reciprocal Rank Fusion), auto-balancing keyword and semantic results without manual weighting
- **MCP Server** — Standard protocol, 14 tools, works with any MCP-compatible Agent
- **Multi-Agent Auto-Sync Plugins** — Claude Code / LangChain / CrewAI / AutoGen / Hermes, all supported
- **CLI Tool** — 15 subcommands (store / search / get / update / delete / list / stats / vacuum / clean / reindex / cleanup / migrate / import / store-batch / search-batch)
- **Data Migration** — Import from holographic memory, generate embeddings for existing memories
- **Auto Deduplication** — Skips duplicate content by default
- **Database Maintenance** — VACUUM, reindex, batch delete by category
- **Content Validation** — Auto-truncation of overly long content (8000 chars)
- **Thread-safe** — check_same_thread=False for multi-agent concurrent access

---

## Project Structure

```text
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
└── tools/                # Data migration & maintenance tools
hermes_plugin/            # Hermes plugin entry (plugin.yaml + re-export)
installers/               # Claude Code installer script
tests/                    # Tests
models/embedding/         # ONNX embedding model (auto-download)
install.sh                # One-liner install script
```

---

## Installation

> **💡 This section is the one-liner install for human readers.** If you want to hand the install instructions to an AI Agent, use the dedicated step-by-step guide in [AGENT_INSTALL.md](AGENT_INSTALL.md) (instructions for AI Agents, language-agnostic).

### One-Liner Script (Recommended)

```bash
# China / Asia users — Gitee + Tsinghua mirror (recommended)
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash

# International users — GitHub + PyPI
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github

# Full install with semantic search
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --with-embedding
```

> For a manual install:
>
> ```bash
> # Or clone manually
> git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
> cd ~/.local/share/sinomem
> python3 -m venv .venv
> .venv/bin/pip install -e .
> ```
>
> The repo is installed to `~/.local/share/sinomem/` by default. The install script automatically adds `.venv/bin` to PATH and configures pip/HuggingFace mirrors for China. After refreshing your terminal, the `sinomem` command is available directly.

> **💡 If you're using Hermes Agent**, we recommend installing via the **Memory Provider plugin** for a better integration experience (auto sync, in-process calls, tool deduplication). See [Hermes Memory Provider Adapter Guide](HERMES_ADAPTER.md).

> **🤖 For the full step-by-step install guide for AI Agents**, see [AGENT_INSTALL.md](AGENT_INSTALL.md).

---

## Download Embedding Model (Optional, for Semantic Search)

Two embedding models are supported — choose one based on your use case (the system auto-detects model type):

| Model | Size | Dim | Language | Best For |
|-------|------|-----|----------|----------|
| **paraphrase-multilingual-MiniLM-L12-v2** | ~113MB | 384 | 50+ languages | Mixed-language content, Chinese + English |
| **bge-small-zh-v1.5** | ~24MB | 512 | Chinese-optimized | Primarily Chinese, smaller size, better Chinese accuracy |

```bash
# Create model directory
mkdir -p models/embedding/onnx

# China users: set HuggingFace mirror (hf-mirror.com is stable and reliable)
export HF_ENDPOINT="https://hf-mirror.com"

# Install download tool (China users: use Tsinghua pip mirror)
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple huggingface-hub

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

> **💡 Mirror tips**:
> - `HF_ENDPOINT=https://hf-mirror.com` — HuggingFace mirror for China (stable and reliable)
> - `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple` — Tsinghua PyPI mirror
> - Users outside China can omit these mirror settings and use the official sources directly.
>
> Without the model, semantic search degrades gracefully to keyword search.

---

## Manual Hermes MCP Config

Add to `~/.hermes/config.yaml` under `mcp_servers:`:

> **📌 Tip**: paste the config below as a **child** of `mcp_servers:` — keep the YAML indentation as shown.

```yaml
sinomem:
  args: []
  command: ~/.local/share/sinomem/.venv/bin/python -m sinomem.entrypoints.mcp_server
```

Restart Hermes to activate.

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
from sinomem.plugins.langchain import SinoMemory

agent = create_react_agent(llm, tools, memory=SinoMemory())
```

### CrewAI (one-line import)

```python
from sinomem.plugins.crewai import SinoCrewMemory

crew = Crew(agents=[...], tasks=[...], memory=SinoCrewMemory())
```

### AutoGen (one-line import)

```python
from sinomem.plugins.autogen import SinoAutoGenMemory

assistant = AssistantAgent(name="agent", memory_provider=SinoAutoGenMemory())
```

### Generic Python API

```python
from sinomem.plugins import create_plugin

plugin = create_plugin()
plugin.auto_store("User prefers Docker")
results = plugin.auto_search("deployment tools")
```

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

# Get / update / delete a memory
sinomem get 1
sinomem update 1 --importance 0.8
sinomem delete 1

# Stats
sinomem stats

# List all memories
sinomem list

# Batch import (JSON file)
sinomem store-batch --file memories.json

# Batch search
sinomem search-batch "feishu" "Docker" "Python"

# Clean up expired memories
sinomem cleanup

# Rebuild FTS5 index (after updating dictionaries)
sinomem reindex

# Reclaim disk space after deletes
sinomem vacuum
```

> 💡 `sino` is a shorthand alias for `sinomem` — both are equivalent.

### MCP Server (Agent auto-calls)

Once configured, the Agent can call these 14 tools directly:

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
| `vacuum_memory` | Reclaim disk space from deleted memories |
| `delete_all_memories` | Delete all memories (⚠️ irreversible) |

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

---

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
| pip package | sinomem | Uninstalls from both<br>system pip and Hermes venv |
| Install directory | `~/.local/share/sinomem/` | Removes all project files |
| Environment variables | SINOMEM_HOME /<br>PATH / HF_ENDPOINT | Removes from `.bashrc` /<br>`.zshrc` / `.profile` |
| Hermes plugin | `~/.hermes/plugins/sinomem` | Removes symlink |
| Memory database | `~/.sinomem/memory.db` | **Interactive prompt** —<br>keep or delete |
| Hermes deps | jieba / tokenizers | Uninstalls from Hermes venv<br>(installed by install.sh) |
| Claude Code hooks | `settings.local.json` | Detects and prompts for cleanup<br>(stale hooks cause errors) |
| jieba cache | `~/.cache/jieba` | Asks before cleaning |

> 💡 Before deleting the database, the script shows memory count and file size, and requires a second confirmation. You can keep the database and reuse it after reinstalling.

---

## FAQ

### Q1: Can I still use semantic search without downloading an embedding model?

Yes. Without the model, semantic search degrades gracefully to keyword search. Download a model (~24MB min) whenever you need semantic search.

### Q2: How do I use SinoMem as Hermes' Memory Provider?

The **Hermes Memory Provider plugin** is the recommended way — see the [Hermes Memory Provider Adapter Guide](HERMES_ADAPTER.md). You can also configure SinoMem as an MCP Server (see [Manual Hermes MCP Config](#manual-hermes-mcp-config)).

### Q3: Can multiple agents share the same memory?

Yes. SinoMem stores data in a single SQLite file (WAL mode) and supports multi-agent concurrent access (check_same_thread=False). One `.db` file can be shared across Claude Code, Cursor, Cline, and Hermes.

### Q4: How do I migrate from other memory systems?

Use `sinomem import` to import from holographic memory, and `sinomem migrate` to generate embeddings for existing memories. See [Data Migration](#data-migration).

### Q5: Does SinoMem call any cloud APIs?

No. All data is stored 100% locally, and embeddings are computed with a local ONNX model — zero API calls, zero cost.

### Q6: I get "sinomem: command not found" after install

The installer modifies the `PATH` environment variable — **open a new terminal window** (or run `source ~/.bashrc`) for it to take effect. You can also invoke it via the full path:

```bash
~/.local/share/sinomem/.venv/bin/sinomem
```

### Q7: MCP Server fails to start — virtual environment not found?

Make sure the one-liner install script finished completely; **do not move or rename** the `~/.local/share/sinomem` directory, otherwise the absolute paths in the MCP Server config will break. If you already moved it, re-run the install script to repair.

---

## Roadmap

- [x] SQLite + FTS5 Chinese full-text search (jieba tokenization)
- [x] Local ONNX semantic search (optional install, dual-mode auto-detection)
- [x] Hybrid search (RRF — Reciprocal Rank Fusion)
- [x] MCP Server (14 tools)
- [x] Multi-agent auto-sync plugins (Claude Code / LangChain / Hermes)
- [x] One-liner install & uninstall scripts
- [ ] CrewAI / AutoGen plugin polish (currently WIP)
- [ ] Record a CLI demo GIF (stored at `assets/demo.gif`)
- [ ] More embedding model support
- [ ] Memory visualization panel

---

## Contributing

Contributions are welcome! Whether it's reporting a bug, improving docs, or adding a feature, your participation is appreciated.

- 🐛 Found a bug → open an [Issue](https://gitee.com/P1M0U/SinoMem/issues)
- ✨ New feature / improvement → open a [PR](https://gitee.com/P1M0U/SinoMem/pulls)
- 📝 Docs or demo assets → submit a PR directly (place GIFs and other media under `assets/`)

Beginner-friendly tasks are labeled with **good first issue** — new contributors are welcome!

**Development conventions**: keep the design modular with high cohesion and low coupling; run `ruff check` and `ruff format` on every `.py` file before committing; follow the Conventional Commits spec.

---

## License

[Apache 2.0](LICENSE)

Copyright © 2026 [P1M0U](https://github.com/P1M0U) · [Gitee](https://gitee.com/P1M0U)

---

## Contact

- Email: [p1m0u@foxmail.com](mailto:p1m0u@foxmail.com)
- GitHub: [https://github.com/P1M0U/SinoMem](https://github.com/P1M0U/SinoMem)
- Gitee: [https://gitee.com/P1M0U/SinoMem](https://gitee.com/P1M0U/SinoMem)
