#!/usr/bin/env bash
# =============================================================================
# Agent Memory Lite — 一键安装脚本
#
# 用法:
#   curl -fsSL https://gitee.com/P1M0U/Agent-Memory-Lite/raw/main/install.sh | bash
#
#   或指定镜像源:
#   curl -fsSL ... | bash -s -- --mirror github
#
# 安装内容:
#   1. 克隆项目到 ~/.local/share/agent-memory-lite/
#   2. pip install -e . 安装核心包（含 CLI 命令 aml）
#   3. 自动配置 shell 环境变量
#   4. 询问是否安装 embedding 可选依赖（语义搜索）
# =============================================================================

set -euo pipefail

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ── 配置 ──
INSTALL_DIR="${AML_HOME:-$HOME/.local/share/agent-memory-lite}"
GITEE_URL="https://gitee.com/P1M0U/Agent-Memory-Lite.git"
GITHUB_URL="https://github.com/P1M0U/Agent-Memory-Lite.git"
REPO_URL="$GITEE_URL"  # 默认 Gitee（国内快）

# ── 参数解析 ──
WITH_EMBEDDING="ask"  # ask | yes | no
MIRROR="gitee"

for arg in "${@}"; do
    case "$arg" in
        --mirror=*)
            MIRROR="${arg#*=}"
            ;;
        --mirror)
            MIRROR="github"
            ;;
        --with-embedding)
            WITH_EMBEDDING="yes"
            ;;
        --no-embedding)
            WITH_EMBEDDING="no"
            ;;
        --help|-h)
            echo "用法: bash install.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --mirror=gitee|github  选择下载源（默认 gitee）"
            echo "  --with-embedding       直接安装语义搜索依赖"
            echo "  --no-embedding          跳过语义搜索依赖"
            echo "  --help                 显示此帮助"
            exit 0
            ;;
    esac
done

if [ "$MIRROR" = "github" ]; then
    REPO_URL="$GITHUB_URL"
fi

# ── Banner ──
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ${BOLD}Agent Memory Lite — 一键安装${NC}${BLUE}          ║${NC}"
echo -e "${BLUE}║  轻量级中文 Agent 记忆增强系统           ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ── 前置检查 ──
echo -e "${BOLD}[1/5]${NC} 检查环境..."

# Python 版本
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        ver=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "0")
        major=$("$candidate" -c "import sys; print(sys.version_info.major)" 2>/dev/null || echo "0")
        if [ "$major" -ge 3 ]; then
            minor=$("$candidate" -c "import sys; print(sys.version_info.minor)" 2>/dev/null || echo "0")
            if [ "$minor" -ge 11 ]; then
                PYTHON="$candidate"
                break
            fi
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo ""
    echo -e "${RED}╔══════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  Python >= 3.11 未找到                   ║${NC}"
    echo -e "${RED}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  当前 Python 版本: $("python3" --version 2>/dev/null || echo "未安装")"
    echo ""
    echo -e "${BOLD}  原因${NC}：agent-memory-lite 使用了 Python 3.11 特性"
    echo -e "        （datetime.UTC / PEP 615），无法降级运行。"
    echo ""
    echo -e "${BOLD}  请选择以下方式之一安装 Python 3.11+：${NC}"
    echo ""
    echo "  ─── Ubuntu / Debian ───"
    echo "  sudo add-apt-repository -y ppa:deadsnakes/ppa"
    echo "  sudo apt update && sudo apt install -y python3.11 python3.11-venv"
    echo ""
    echo "  ─── macOS ───"
    echo "  brew install python@3.11"
    echo ""
    echo "  ─── 通用（pyenv）───"
    echo "  curl https://pyenv.run | bash"
    echo "  pyenv install 3.11"
    echo "  pyenv global 3.11"
    echo ""
    echo "  安装完成后重新运行本脚本即可。"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} Python $("$PYTHON" --version)"

# pip
if ! "$PYTHON" -m pip --version &>/dev/null; then
    echo -e "${RED}✗ pip 不可用，请先安装 pip${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} pip 可用"

# 升级 pip，避免旧版与 setuptools-scm 不兼容导致 PEP 660 editable install 失败
echo -e "  正在升级 pip..."
"$PYTHON" -m pip install --quiet --upgrade pip 2>&1 | tail -1
echo -e "  ${GREEN}✓${NC} pip 已升级到最新版"

# git
if ! command -v git &>/dev/null; then
    echo -e "${RED}✗ 未找到 git，请先安装 git${NC}"
    exit 1
fi
echo -e "  ${GREEN}✓${NC} git 可用"

echo ""

# ── 克隆 / 更新仓库 ──
echo -e "${BOLD}[2/5]${NC} 同步仓库..."

if [ -d "$INSTALL_DIR/.git" ]; then
    echo -e "  ${YELLOW}!${NC} 已有安装，执行 git pull 更新..."
    git -C "$INSTALL_DIR" pull --ff-only 2>/dev/null || {
        echo -e "  ${YELLOW}!${NC} git pull 失败，重新 clone..."
        rm -rf "$INSTALL_DIR"
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
    }
else
    echo -e "  克隆到 ${INSTALL_DIR}..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --depth 1 "$REPO_URL" "$INSTALL_DIR"
fi

echo -e "  ${GREEN}✓${NC} 仓库就绪: $INSTALL_DIR"
echo ""

# ── pip install ──
echo -e "${BOLD}[3/5]${NC} 安装 Python 包..."

cd "$INSTALL_DIR"

# 构建安装参数
INSTALL_ARGS=("-e" ".")
EXTRA_NAME=""

# embedding 依赖询问
if [ "$WITH_EMBEDDING" = "ask" ]; then
    echo ""
    echo -e "  ${YELLOW}是否安装语义搜索依赖（onnxruntime + sqlite-vec）？${NC}"
    echo -e "  安装后可启用 semantic/hybrid 搜索模式，但会增加 ~200MB 磁盘占用。"
    echo -n "  安装 embedding 依赖？[y/N] "
    read -r answer </dev/tty || answer="n"
    if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
        WITH_EMBEDDING="yes"
    else
        WITH_EMBEDDING="no"
    fi
fi

if [ "$WITH_EMBEDDING" = "yes" ]; then
    INSTALL_ARGS=("-e" ".[embedding]")
    EXTRA_NAME="（含 embedding）"
fi

echo ""
echo -e "  pip install ${INSTALL_ARGS[*]} ..."
"$PYTHON" -m pip install --quiet "${INSTALL_ARGS[@]}" 2>&1 | tail -3

# 验证安装
if "$PYTHON" -c "import agent_memory_lite" 2>/dev/null; then
    VER=$("$PYTHON" -c "from agent_memory_lite import __version__; print(__version__)" 2>/dev/null || echo "?")
    echo -e "  ${GREEN}✓${NC} agent-memory-lite ${VER} 安装成功${EXTRA_NAME}"
else
    echo -e "${RED}✗ 安装验证失败，请检查上方错误信息${NC}"
    exit 1
fi

echo ""

# ── 环境变量 ──
echo -e "${BOLD}[4/5]${NC} 配置环境变量..."

SHELL_RC=""
case "$SHELL" in
    */zsh) SHELL_RC="$HOME/.zshrc" ;;
    */bash) SHELL_RC="$HOME/.bashrc" ;;
    *) SHELL_RC="$HOME/.profile" ;;
esac

ENV_BLOCK_START="# >>> Agent Memory Lite >>>"
ENV_BLOCK_END="# <<< Agent Memory Lite <<<"
ENV_CONTENT="${ENV_BLOCK_START}
export AML_HOME=\"${INSTALL_DIR}\"
export PATH=\"\${AML_HOME}/.venv/bin:\${PATH}\"
${ENV_BLOCK_END}"

if grep -q "$ENV_BLOCK_START" "$SHELL_RC" 2>/dev/null; then
    # 更新已有 block
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/c\\
$ENV_CONTENT" "$SHELL_RC"
    else
        sed -i "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/c\\
$ENV_CONTENT" "$SHELL_RC"
    fi
    echo -e "  ${YELLOW}!${NC} 已更新 $SHELL_RC 中的 AML_HOME"
else
    echo "" >> "$SHELL_RC"
    echo "$ENV_CONTENT" >> "$SHELL_RC"
    echo -e "  ${GREEN}✓${NC} 已添加 AML_HOME 到 $SHELL_RC"
fi

echo ""

# ── Hermes 插件配置提示 ──
echo -e "${BOLD}[5/5]${NC} 检查插件配置..."
echo ""

if [ -d "$HOME/.hermes" ] || [ -n "${HERMES_HOME:-}" ]; then
    HERMES_BASE="${HERMES_HOME:-$HOME/.hermes}"
    HERMES_PLUGIN_DIR="$HERMES_BASE/plugins"
    echo -e "  ${GREEN}✓${NC} 检测到 Hermes 环境"
    echo ""

    # 自动符号链接 hermes_plugin
    PLUGIN_LINK="$HERMES_PLUGIN_DIR/agent-memory-lite"
    if [ -L "$PLUGIN_LINK" ] || [ -d "$PLUGIN_LINK" ]; then
        echo -e "  ${YELLOW}!${NC} Hermes 插件已存在，跳过链接"
    else
        mkdir -p "$HERMES_PLUGIN_DIR"
        ln -s "$INSTALL_DIR/hermes_plugin" "$PLUGIN_LINK"
        echo -e "  ${GREEN}✓${NC} 已链接 Hermes 插件 → ${PLUGIN_LINK}"
    fi

    # 自动安装 agent-memory-lite 到 Hermes venv
    # （Hermes 插件在 Hermes 进程中运行，需要能 import agent_memory_lite）
    HERMES_VENV=""
    for venv_path in \
        "$HERMES_BASE/hermes-agent/venv" \
        "$HERMES_BASE/venv" \
        "$HERMES_BASE/.venv"; do
        if [ -f "$venv_path/bin/python" ]; then
            HERMES_VENV="$venv_path"
            break
        fi
    done

    if [ -n "$HERMES_VENV" ]; then
        HERMES_PYTHON="$HERMES_VENV/bin/python"
        echo ""
        echo -e "  ${BOLD}安装到 Hermes venv：${NC}"
        echo "  ────────────────────────────────────────────"

        # 先安装轻量依赖（jieba + tokenizers）
        echo "  安装基础依赖..."
        "$HERMES_PYTHON" -m pip install --quiet --upgrade pip 2>&1 | tail -1
        "$HERMES_PYTHON" -m pip install --quiet jieba tokenizers 2>&1 | tail -3

        # 安装 agent-memory-lite 包本身到 Hermes venv
        echo "  安装 agent-memory-lite（可编辑模式）..."
        "$HERMES_PYTHON" -m pip install --quiet -e "$INSTALL_DIR" 2>&1 | tail -3

        if "$HERMES_PYTHON" -c "import agent_memory_lite" 2>/dev/null; then
            echo -e "  ${GREEN}✓${NC} Hermes venv 配置完成（${HERMES_VENV}）"
        else
            echo -e "  ${YELLOW}!${NC} Hermes venv 安装验证失败，请手动执行："
            echo "    ${HERMES_PYTHON} -m pip install -e ${INSTALL_DIR}"
        fi
        echo "  ────────────────────────────────────────────"
    else
        echo ""
        echo -e "  ${YELLOW}!${NC} 未找到 Hermes venv，请手动安装依赖到 Hermes："
        echo "    <hermes-venv>/bin/pip install jieba tokenizers"
        echo "    <hermes-venv>/bin/pip install -e ${INSTALL_DIR}"
    fi
else
    echo -e "  ${BLUE}ℹ${NC} 未检测到 Hermes，跳过插件配置"
    echo "  （如果你使用 Hermes，请将 hermes_plugin/ 链接到 Hermes 插件目录）"
fi

echo ""

# ── 模型下载提示 ──
if [ "$WITH_EMBEDDING" = "yes" ]; then
    echo -e "${BOLD}嵌入模型：${NC}"
    ONNX_DIR="$INSTALL_DIR/models/embedding/onnx"
    if [ -f "$ONNX_DIR/model_quantized.onnx" ] || [ -f "$ONNX_DIR/model_quint8_avx2.onnx" ] || [ -f "$ONNX_DIR/model.onnx" ]; then
        echo -e "  ${GREEN}✓${NC} ONNX 模型已就绪"
    else
        echo -e "  ${YELLOW}!${NC} ONNX 模型未下载，语义搜索将自动降级为关键词搜索"
        echo "  下载方法: cd ${INSTALL_DIR} && python -c \"from agent_memory_lite.core.embedder import ensure_model; ensure_model()\""
    fi
    echo ""
fi

# ── 完成 ──
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ${BOLD}安装完成！${NC}${GREEN}                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}快速开始：${NC}"
echo "  ────────────────────────────────────────────"
echo "  新终端执行:  source ${SHELL_RC}  （刷新环境变量）"
echo ""
echo "  CLI 命令:"
echo "    aml store \"用户喜欢 Python 编程\" -c user_pref"
echo "    aml search \"Python\" -m hybrid"
echo "    aml list"
echo "    aml stats"
echo "  ────────────────────────────────────────────"
echo ""
echo -e "  ${BOLD}更新：${NC}"
echo "    cd ${INSTALL_DIR} && git pull && pip install -e ."
echo "  ────────────────────────────────────────────"
echo ""
