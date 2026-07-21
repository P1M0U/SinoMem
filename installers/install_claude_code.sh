#!/usr/bin/env bash
# =============================================================================
# SinoMem — Claude Code 自动记忆同步一键安装
#
# 安装后，Claude Code 将自动：
#   1. 每次对话前 — 检索相关记忆注入 prompt
#   2. 写入文件时 — 自动捕获记忆内容
#   3. 会话结束时 — 自动持久化会话摘要
#
# 用法：
#   bash installers/install_claude_code.sh
#   bash installers/install_claude_code.sh --global   # 安装到 ~/.claude/
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PLUGIN_DIR="$PROJECT_ROOT/sinomem/plugins/claude_code"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE} SinoMem — Claude Code 自动同步${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# ── 确定安装目标 ──
if [[ "${1:-}" == "--global" ]]; then
    TARGET_DIR="$HOME/.claude"
    echo -e "安装模式: ${YELLOW}全局 (~/.claude/)${NC}"
else
    TARGET_DIR="$(pwd)/.claude"
    echo -e "安装模式: ${YELLOW}项目本地 (.claude/)${NC}"
fi

mkdir -p "$TARGET_DIR"
echo ""

# ── 备份现有配置 ──
SETTINGS_FILE="$TARGET_DIR/settings.local.json"
SETTINGS_BAK="${SETTINGS_FILE}.bak.$(date +%Y%m%d_%H%M%S)"

if [[ -f "$SETTINGS_FILE" ]]; then
    cp "$SETTINGS_FILE" "$SETTINGS_BAK"
    echo -e "${GREEN}✓${NC} 已备份现有配置 → ${SETTINGS_BAK}"
fi

# ── 生成/更新 settings.local.json ──
PYTHON_BIN="${SINOMEM_PYTHON:-python3}"

# Claude Code hooks 配置
HOOKS_CONFIG=$(cat <<EOF
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "command": "${PYTHON_BIN} ${PLUGIN_DIR}/inject_memory.py"
      }]
    }],
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "command": "${PYTHON_BIN} ${PLUGIN_DIR}/capture_write.py"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "command": "${PYTHON_BIN} ${PLUGIN_DIR}/persist_session.py"
      }]
    }]
  }
}
EOF
)

# 读取现有配置或新建
if [[ -f "$SETTINGS_FILE" ]]; then
    echo -e "${YELLOW}!${NC} 检测到已有 settings.local.json，手动合并..."
    echo ""
    echo "请手动将以下 hooks 配置合并到 $SETTINGS_FILE："
    echo "────────────────────────────────────────────"
    echo "$HOOKS_CONFIG"
    echo "────────────────────────────────────────────"
else
    echo "$HOOKS_CONFIG" > "$SETTINGS_FILE"
    echo -e "${GREEN}✓${NC} 已创建 $SETTINGS_FILE"
fi

# ── 验证 Python 环境 ──
echo ""
echo "检查 Python 环境..."
if $PYTHON_BIN -c "from sinomem.plugins.base import BasePlugin; print('OK')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} sinomem 导入成功"
else
    echo -e "${YELLOW}!${NC} sinomem 未在 Python 路径中"
    echo "  请确保已安装: pip install sinomem"
    echo "  或设置环境变量: export SINOMEM_HOME=$PROJECT_ROOT"
fi

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN} 安装完成！${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "自动同步已启用："
echo "  • 对话前 → 自动检索相关记忆注入 prompt"
echo "  • 写入文件 → 自动捕获记忆内容"
echo "  • 会话结束 → 自动持久化会话摘要"
echo ""
echo "如需卸载或禁用，请删除 hooks 配置："
echo "  $SETTINGS_FILE"
