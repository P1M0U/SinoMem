# SinoMem Step-by-Step Install Guide for AI Agents

> This document contains the **step-by-step install instructions** for AI Agents (Claude Code, Cursor, Cline, etc.). Human readers can skip this file and use the one-liner install commands in the main [README_EN.md](README_EN.md).

Copy the prompt below and send it to your AI Agent — it will handle the install automatically.

> **💡 If you're using Hermes Agent**, we recommend installing via the **Memory Provider plugin** for a better integration experience (auto sync, in-process calls, tool deduplication). See [Hermes Memory Provider Adapter Guide](HERMES_ADAPTER.md).

## Option A: One-Liner Script (Recommended)

```
Please install SinoMem for me, run:

# China / Asia users (Gitee + Tsinghua pip mirror):
curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --with-embedding

# International users (GitHub + PyPI):
curl -fsSL https://github.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --mirror github --with-embedding

After install, run source ~/.bashrc (or ~/.zshrc) to refresh PATH, then verify with sinomem --help.
Tell me the result when done.
```

## Option B: Install from GitHub

```
Please install SinoMem for me. Steps:

1. Clone and set up virtual environment
   git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   python3 -m venv .venv

2. If in China, configure pip mirror first for faster downloads:
   .venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   .venv/bin/pip install -e .

3. Verify the installation works
   .venv/bin/python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

4. Add sinomem CLI to PATH, append to ~/.bashrc or ~/.zshrc:
   export SINOMEM_HOME="$HOME/.local/share/sinomem"
   export PATH="$SINOMEM_HOME/.venv/bin:$PATH"
   # China users also add:
   export HF_ENDPOINT="https://hf-mirror.com"

5. Ask the user whether to install embedding dependencies (for semantic search):
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. Install (onnxruntime + sqlite-vec, ~200MB)

6. If user picked B, run .venv/bin/pip install -e ".[embedding]", then ask if they want to auto-download the ONNX model (~24MB):
   # China users: set HF_ENDPOINT mirror first
   export HF_ENDPOINT="https://hf-mirror.com"
   .venv/bin/pip install huggingface-hub
   .venv/bin/python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

7. Ask the user to choose an install method:
   — A. Hermes Memory Provider plugin (recommended) — Run `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server — Continue with step 8-9

8. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   sinomem:
     args: []
     command: ~/.local/share/sinomem/.venv/bin/python -m sinomem.entrypoints.mcp_server

9. Run source ~/.bashrc (or ~/.zshrc) to refresh PATH, then verify with sinomem --help.

Tell me the result when done.
```

## Option C: Install from Gitee (faster in China)

```
Please install SinoMem for me. Steps:

1. Clone via Gitee and set up virtual environment (fast in China)
   git clone --depth 1 https://gitee.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   python3 -m venv .venv

2. Configure pip mirror and install
   .venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   .venv/bin/pip install -e .

3. Verify the installation works
   .venv/bin/python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

4. Add sinomem CLI to PATH, append to ~/.bashrc or ~/.zshrc:
   export SINOMEM_HOME="$HOME/.local/share/sinomem"
   export PATH="$SINOMEM_HOME/.venv/bin:$PATH"
   export HF_ENDPOINT="https://hf-mirror.com"  # HuggingFace mirror for China

5. Ask the user whether to install embedding dependencies (for semantic search):
   — A. Skip (default) — semantic search degrades gracefully to keyword search
   — B. Install (onnxruntime + sqlite-vec, ~200MB)

6. If user picked B, run .venv/bin/pip install -e ".[embedding]", then ask if they want to auto-download the ONNX model (~24MB):
   export HF_ENDPOINT="https://hf-mirror.com"
   .venv/bin/pip install huggingface-hub
   .venv/bin/python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

7. Ask the user to choose an install method:
   — A. Hermes Memory Provider plugin (recommended) — Run `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server — Continue with step 8-9

8. (Only if user chose MCP Server) Add MCP Server config to ~/.hermes/config.yaml under mcp_servers:
   sinomem:
     args: []
     command: ~/.local/share/sinomem/.venv/bin/python -m sinomem.entrypoints.mcp_server

9. Run source ~/.bashrc (or ~/.zshrc) to refresh PATH, then verify with sinomem --help.

Tell me the result when done.
```

---

## Related Links

- [Back to main README (Quick Start)](README_EN.md)
- [Hermes Memory Provider Adapter Guide](HERMES_ADAPTER.md)
