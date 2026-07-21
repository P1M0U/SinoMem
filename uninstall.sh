#!/usr/bin/env bash
# =============================================================================
# SinoMem — 一键卸载脚本
#
# 用法:
#   curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/uninstall.sh | bash
#
#   或本地执行:
#   bash uninstall.sh
#
# 卸载内容:
#   1. pip 卸载 sinomem 包（系统 + Hermes venv）
#   2. 删除安装目录 ~/.local/share/sinomem/
#   3. 清理 shell 环境变量（SINOMEM_HOME / PATH / HF_ENDPOINT）
#   4. 移除 Hermes 插件符号链接
#   5. 询问是否保留记忆数据库文件
#   6. 卸载 Hermes venv 中的 jieba / tokenizers 依赖
#   7. 清理 Claude Code hooks 配置
#   8. 询问是否清理 jieba 缓存
# =============================================================================

set -euo pipefail

# ── 颜色 ──
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ── 默认路径（与 install.sh 保持一致）──
INSTALL_DIR="${SINOMEM_HOME:-$HOME/.local/share/sinomem}"
DB_PATH="${SINOMEM_DB_PATH:-$HOME/.sinomem/memory.db}"
JIEBA_CACHE="$HOME/.cache/jieba"
HERMES_PLUGIN_LINK="$HOME/.hermes/plugins/sinomem"

# ── Banner ──
echo ""
echo -e "${BLUE}╔══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  ${BOLD}SinoMem — 一键卸载${NC}${BLUE}          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════╝${NC}"
echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 1: pip 卸载
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[1/7]${NC} pip 卸载 sinomem..."

# 系统 pip 卸载
UNINSTALLED=0
for pip_cmd in pip3 pip; do
    if command -v "$pip_cmd" &>/dev/null; then
        if "$pip_cmd" show sinomem &>/dev/null 2>&1; then
            echo -e "  卸载系统 pip 安装..."
            "$pip_cmd" uninstall -y sinomem 2>/dev/null && UNINSTALLED=1 || true
            break
        fi
    fi
done

# Hermes venv 卸载
HERMES_VENV=""
for venv_path in \
    "$HOME/.hermes/hermes-agent/venv" \
    "$HOME/.hermes/venv" \
    "$HOME/.hermes/.venv"; do
    if [ -f "$venv_path/bin/python" ]; then
        HERMES_VENV="$venv_path"
        break
    fi
done

if [ -n "$HERMES_VENV" ]; then
    HERMES_PIP="$HERMES_VENV/bin/pip"
    if "$HERMES_PIP" show sinomem &>/dev/null 2>&1; then
        echo -e "  卸载 Hermes venv 中的安装..."
        "$HERMES_PIP" uninstall -y sinomem 2>/dev/null && UNINSTALLED=1 || true
    fi
fi

if [ "$UNINSTALLED" -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} pip 包已卸载"
else
    echo -e "  ${YELLOW}!${NC} 未检测到 pip 安装，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 2: 删除安装目录
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[2/7]${NC} 删除安装目录..."

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  目录: ${INSTALL_DIR}"
    rm -rf "$INSTALL_DIR"
    echo -e "  ${GREEN}✓${NC} 安装目录已删除"
else
    echo -e "  ${YELLOW}!${NC} 安装目录不存在，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 3: 清理 shell 环境变量
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[3/7]${NC} 清理 shell 环境变量..."

ENV_BLOCK_START="# >>> SinoMem >>>"
ENV_BLOCK_END="# <<< SinoMem <<<"

CLEANED_COUNT=0
for rc_file in "$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile"; do
    if [ -f "$rc_file" ] && grep -q "$ENV_BLOCK_START" "$rc_file" 2>/dev/null; then
        echo -e "  清理: ${rc_file}"

        if [[ "$OSTYPE" == "darwin"* ]]; then
            sed -i '' "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/d" "$rc_file"
        else
            sed -i "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/d" "$rc_file"
        fi
        CLEANED_COUNT=$((CLEANED_COUNT + 1))
    fi
done

if [ "$CLEANED_COUNT" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} 已清理 ${CLEANED_COUNT} 个 shell 配置文件"
else
    echo -e "  ${YELLOW}!${NC} 未找到 SinoMem 的环境变量配置，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 4: 移除 Hermes 插件符号链接
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[4/7]${NC} 移除 Hermes 插件..."

if [ -L "$HERMES_PLUGIN_LINK" ]; then
    echo -e "  移除符号链接: ${HERMES_PLUGIN_LINK}"
    rm "$HERMES_PLUGIN_LINK"
    echo -e "  ${GREEN}✓${NC} Hermes 插件链接已移除"
elif [ -d "$HERMES_PLUGIN_LINK" ]; then
    echo -e "  移除目录: ${HERMES_PLUGIN_LINK}"
    rm -rf "$HERMES_PLUGIN_LINK"
    echo -e "  ${GREEN}✓${NC} Hermes 插件目录已移除"
else
    echo -e "  ${YELLOW}!${NC} Hermes 插件未安装，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 5: 记忆数据库 — 询问用户
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[5/7]${NC} 记忆数据库..."

DB_EXISTS=false
if [ -f "$DB_PATH" ]; then
    DB_EXISTS=true
    DB_SIZE=$(du -h "$DB_PATH" 2>/dev/null | cut -f1)
    # 统计记忆条数（如果 sqlite3 可用）
    DB_COUNT="?"
    if command -v sqlite3 &>/dev/null; then
        DB_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM memories;" 2>/dev/null || echo "?")
    fi
fi

if [ "$DB_EXISTS" = true ]; then
    echo ""
    echo -e "  ${YELLOW}╔══════════════════════════════════════════╗${NC}"
    echo -e "  ${YELLOW}║  检测到记忆数据库                        ║${NC}"
    echo -e "  ${YELLOW}╠══════════════════════════════════════════╣${NC}"
    echo -e "  ${YELLOW}║${NC}  路径: ${DB_PATH}"
    echo -e "  ${YELLOW}║${NC}  大小: ${DB_SIZE}"
    echo -e "  ${YELLOW}║${NC}  记忆: ${DB_COUNT} 条"
    echo -e "  ${YELLOW}╚══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "  ${BOLD}是否保留记忆数据库文件？${NC}"
    echo ""
    echo -e "  ${GREEN}[Y]${NC}  保留 — 数据库文件保持不变"
    echo -e "         （重新安装后可继续使用原有记忆）"
    echo ""
    echo -e "  ${RED}[N]${NC}  删除 — 永久删除所有记忆数据"
    echo -e "         （⚠️ 此操作不可逆）"
    echo ""
    echo -n "  保留数据库？[Y/n] "

    read -r answer </dev/tty || answer="y"

    if [ "$answer" = "n" ] || [ "$answer" = "N" ]; then
        # 二次确认
        echo ""
        echo -ne "  ${RED}确认永久删除 ${DB_PATH}？[y/N] ${NC}"
        read -r confirm </dev/tty || confirm="n"
        if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
            rm -f "$DB_PATH"
            # 同时清理 WAL/SHM 文件
            rm -f "${DB_PATH}-wal" "${DB_PATH}-shm"
            echo -e "  ${RED}✓${NC} 数据库已删除"

            # 如果目录为空则清理
            DB_DIR="$(dirname "$DB_PATH")"
            if [ -d "$DB_DIR" ] && [ -z "$(ls -A "$DB_DIR" 2>/dev/null)" ]; then
                rmdir "$DB_DIR" 2>/dev/null || true
            fi
        else
            echo -e "  ${GREEN}✓${NC} 数据库已保留（取消删除）"
        fi
    else
        echo -e "  ${GREEN}✓${NC} 数据库已保留: ${DB_PATH}"
        echo ""
        echo -e "  ${BLUE}ℹ${NC}  重新安装后可直接使用原有记忆："
        echo "     curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash"
    fi
else
    echo -e "  ${YELLOW}!${NC} 数据库不存在，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 6: 清理 Hermes venv 中由 install.sh 安装的依赖
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[6/7]${NC} 清理 Hermes venv 依赖..."

HERMES_DEPS_CLEANED=0
if [ -n "$HERMES_VENV" ]; then
    HERMES_PIP="$HERMES_VENV/bin/pip"
    for pkg in jieba tokenizers; do
        if "$HERMES_PIP" show "$pkg" &>/dev/null 2>&1; then
            echo -e "  卸载 Hermes venv 中的 ${pkg}..."
            "$HERMES_PIP" uninstall -y "$pkg" 2>/dev/null && HERMES_DEPS_CLEANED=1 || true
        fi
    done
fi

if [ "$HERMES_DEPS_CLEANED" -eq 1 ]; then
    echo -e "  ${GREEN}✓${NC} Hermes venv 依赖已清理"
else
    echo -e "  ${YELLOW}!${NC} 未检测到 Hermes venv 中的额外依赖，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 步骤 7: 清理 Claude Code hooks（install_claude_code.sh 安装的）
# ══════════════════════════════════════════════════════════════════════════════
echo -e "${BOLD}[7/7]${NC} 检查 Claude Code hooks..."

CC_CLEANED=0
for cc_dir in "$HOME/.claude" "$(pwd)/.claude"; do
    CC_SETTINGS="$cc_dir/settings.local.json"
    if [ -f "$CC_SETTINGS" ] && grep -q "sinomem" "$CC_SETTINGS" 2>/dev/null; then
        echo ""
        echo -e "  ${YELLOW}╔══════════════════════════════════════════╗${NC}"
        echo -e "  ${YELLOW}║  检测到 Claude Code hooks 引用 sinomem    ║${NC}"
        echo -e "  ${YELLOW}╠══════════════════════════════════════════╣${NC}"
        echo -e "  ${YELLOW}║${NC}  文件: ${CC_SETTINGS}"
        echo -e "  ${YELLOW}╚══════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "  ${BOLD}是否清理 Claude Code hooks 配置？${NC}"
        echo -e "  （卸载后残留 hooks 会导致 Claude Code 报错）"
        echo -ne "  清理 hooks？[Y/n] "

        read -r cc_answer </dev/tty || cc_answer="y"

        if [ "$cc_answer" = "n" ] || [ "$cc_answer" = "N" ]; then
            echo -e "  ${YELLOW}!${NC} 已跳过，请手动清理: ${CC_SETTINGS}"
        else
            # 备份后删除
            cp "$CC_SETTINGS" "${CC_SETTINGS}.bak.$(date +%Y%m%d_%H%M%S)"
            rm "$CC_SETTINGS"
            echo -e "  ${GREEN}✓${NC} Claude Code hooks 已清理（原文件已备份）"
            CC_CLEANED=1
        fi
    fi
done

if [ "$CC_CLEANED" -eq 0 ]; then
    echo -e "  ${YELLOW}!${NC} 未检测到 Claude Code hooks 引用 sinomem，跳过"
fi

echo ""

# ══════════════════════════════════════════════════════════════════════════════
# 额外清理（静默 + 可选）
# ══════════════════════════════════════════════════════════════════════════════

# jieba 缓存（由 jieba 分词库在运行时自动创建）
if [ -d "$JIEBA_CACHE" ]; then
    JIEBA_CACHE_SIZE=$(du -sh "$JIEBA_CACHE" 2>/dev/null | cut -f1)
    echo -e "  ${YELLOW}!${NC} 检测到 jieba 分词缓存: ${JIEBA_CACHE} (${JIEBA_CACHE_SIZE})"
    echo -e "  （此缓存由 jieba 库自动创建，其他程序也可能使用）"
    echo -ne "  是否清理？[y/N] "
    read -r jieba_answer </dev/tty || jieba_answer="n"
    if [ "$jieba_answer" = "y" ] || [ "$jieba_answer" = "Y" ]; then
        rm -rf "$JIEBA_CACHE"
        echo -e "  ${GREEN}✓${NC} jieba 缓存已清理"
    else
        echo -e "  ${YELLOW}!${NC} 已保留 jieba 缓存"
    fi
    echo ""
fi

# ── 完成 ──
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ${BOLD}卸载完成！${NC}${GREEN}                           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}已清理的内容：${NC}"
echo "  ────────────────────────────────────────────"
echo "  ✓ pip 包 (sinomem)"
echo "  ✓ 安装目录 (${INSTALL_DIR})"
echo "  ✓ shell 环境变量 (SINOMEM_HOME / PATH / HF_ENDPOINT)"
echo "  ✓ Hermes 插件链接"
echo "  ✓ Hermes venv 依赖 (jieba / tokenizers)"
echo "  ✓ Claude Code hooks"
echo "  ────────────────────────────────────────────"
echo ""
echo -e "  ${BOLD}提示：${NC}"
echo "    请手动执行以下命令刷新当前终端环境变量："
echo "      source ~/.bashrc    (bash 用户)"
echo "      source ~/.zshrc     (zsh 用户)"
echo ""
echo -e "  ${BOLD}重新安装：${NC}"
echo "    curl -fsSL https://gitee.com/P1M0U/SinoMem/raw/main/install.sh | bash"
echo ""
