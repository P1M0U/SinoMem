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
#   1. pip 卸载 sinomem 包
#   2. 删除安装目录 ~/.local/share/sinomem/
#   3. 清理 shell 环境变量（SINOMEM_HOME / PATH / HF_ENDPOINT）
#   4. 移除 Hermes 插件符号链接
#   5. 询问是否保留记忆数据库文件
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
echo -e "${BOLD}[1/5]${NC} pip 卸载 sinomem..."

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
echo -e "${BOLD}[2/5]${NC} 删除安装目录..."

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
echo -e "${BOLD}[3/5]${NC} 清理 shell 环境变量..."

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
echo -e "${BOLD}[4/5]${NC} 移除 Hermes 插件..."

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
echo -e "${BOLD}[5/5]${NC} 记忆数据库..."

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
# 额外清理（静默）
# ══════════════════════════════════════════════════════════════════════════════

# pip 缓存中可能残留的 sinomem 构建文件
pip_cache_clean() {
    for pip_cmd in pip3 pip; do
        if command -v "$pip_cmd" &>/dev/null; then
            "$pip_cmd" cache purge 2>/dev/null || true
            return
        fi
    done
}
pip_cache_clean

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
