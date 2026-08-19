# SinoMem 给智能体执行的完整分步安装指南

> 本文档是给 AI Agent（Claude Code / Cursor / Cline 等）执行的**分步安装指令**。人类读者可跳过本文，直接在主 [README.md](README.md) 中查看一键安装命令。

复制以下内容发给你的 AI Agent，它会自动完成安装。

> **💡 如果你使用的是 Hermes Agent**，推荐通过 **Memory Provider 插件方式**安装，可获得更好的集成体验（自动同步、进程内调用、工具去重）。详见 [Hermes Memory Provider 适配器安装指南](HERMES_ADAPTER.md)。

## 方式一：一键脚本（推荐）

```
请帮我安装 SinoMem 记忆系统，执行以下命令：

curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash -s -- --with-embedding

安装后执行 source ~/.bashrc（或 ~/.zshrc）刷新环境变量，然后运行 sinomem --help 验证 CLI 命令可用。
告诉我结果。
```

## 方式二：从 Gitee 安装（国内更快）

```
请帮我安装 SinoMem 记忆系统，步骤如下：

1. 克隆仓库并创建虚拟环境（使用 Gitee 国内镜像）
   git clone --depth 1 https://gitee.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   python3 -m venv .venv

2. 配置 pip 清华镜像源并安装（国内下载更快）
   .venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   .venv/bin/pip install -e .

3. 验证安装是否成功
   .venv/bin/python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

4. 将 sinomem CLI 加入 PATH，追加到 ~/.bashrc 或 ~/.zshrc：
   export SINOMEM_HOME="$HOME/.local/share/sinomem"
   export PATH="$SINOMEM_HOME/.venv/bin:$PATH"
   export HF_ENDPOINT="https://hf-mirror.com"   # HuggingFace 国内镜像（用于下载模型）

5. 询问用户是否需要安装嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不安装（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. 安装 embedding 依赖（onnxruntime + sqlite-vec，~200MB）

6. 如果用户选择 B，执行 .venv/bin/pip install -e ".[embedding]" 安装依赖。
   然后询问是否需要自动下载 ONNX 模型（约 24MB），如果需要则运行：
   export HF_ENDPOINT="https://hf-mirror.com"
   .venv/bin/pip install huggingface-hub
   .venv/bin/python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

7. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server 方式 — 继续执行以下步骤 8-9

8. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   sinomem:
     args: []
     command: ~/.local/share/sinomem/.venv/bin/python -m sinomem.entrypoints.mcp_server

9. 执行 source ~/.bashrc（或 ~/.zshrc）刷新环境变量，然后运行 sinomem --help 验证 CLI 命令可用。

完成后告诉我安装结果。
```

## 方式三：从 GitHub 安装

```
请帮我安装 SinoMem 记忆系统，步骤如下：

1. 克隆仓库并创建虚拟环境
   git clone --depth 1 https://github.com/P1M0U/SinoMem.git ~/.local/share/sinomem
   cd ~/.local/share/sinomem
   python3 -m venv .venv

2. 配置 pip 镜像源并安装（国内用户推荐清华镜像，国外用户可跳过此步）
   # 国内用户执行:
   .venv/bin/pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
   # 国外用户直接安装:
   .venv/bin/pip install -e .

3. 验证安装是否成功
   .venv/bin/python -c "from sinomem.core.engine import MemoryEngine; print('ok')"

4. 将 sinomem CLI 加入 PATH，追加到 ~/.bashrc 或 ~/.zshrc：
   export SINOMEM_HOME="$HOME/.local/share/sinomem"
   export PATH="$SINOMEM_HOME/.venv/bin:$PATH"
   # 国内用户还需设置 HuggingFace 镜像：
   export HF_ENDPOINT="https://hf-mirror.com"

5. 询问用户是否需要安装嵌入模型（用于语义搜索），给出以下选项让用户选择：
   — A. 不安装（默认）— 跳过此步，语义搜索自动降级为关键词搜索
   — B. 安装 embedding 依赖（onnxruntime + sqlite-vec，~200MB）

6. 如果用户选择 B，执行 .venv/bin/pip install -e ".[embedding]" 安装依赖。
   然后询问是否需要自动下载 ONNX 模型（约 24MB），如果需要则运行：
   # 国内用户先设置镜像：
   export HF_ENDPOINT="https://hf-mirror.com"
   .venv/bin/pip install huggingface-hub
   .venv/bin/python -c "from sinomem.core.embedder import ensure_model; print('ok' if ensure_model() else 'download failed')"

7. 询问用户选择安装方式，给出以下选项：
   — A. Hermes Memory Provider 插件方式（推荐）— 执行 `ln -s ~/.local/share/sinomem/hermes_plugin/ ~/.hermes/plugins/sinomem`
   — B. MCP Server 方式 — 继续执行以下步骤 8-9

8. （仅当用户选择 MCP Server 方式时）把 MCP Server 配置写入 ~/.hermes/config.yaml 的 mcp_servers 段：
   sinomem:
     args: []
     command: ~/.local/share/sinomem/.venv/bin/python -m sinomem.entrypoints.mcp_server

9. 执行 source ~/.bashrc（或 ~/.zshrc）刷新环境变量，然后运行 sinomem --help 验证 CLI 命令可用。

完成后告诉我安装结果。
```

---

## 相关链接

- [返回主 README（快速体验）](README.md)
- [Hermes Memory Provider 适配器安装指南](HERMES_ADAPTER.md)
