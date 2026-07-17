"""Claude Code PostToolUse 钩子 — 自动捕获记忆写入

当 Claude Code 执行 Write/Edit 操作时，检查是否写入了值得记忆的内容，
自动存储到 Agent Memory Lite。

配置方式（~/.claude/settings.json 或项目 .claude/settings.json）:

{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "command": "python3 ~/.cli/agent-memory-lite/plugins/claude_code/capture_write.py"
      }]
    }]
  }
}
"""

import json
import sys

# 优先从已安装的包导入，回退到 sys.path
try:
    from agent_memory_lite.plugins.base import BasePlugin
except ImportError:
    from pathlib import Path

    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from agent_memory_lite.plugins.base import BasePlugin  # noqa: E402

# 值得记忆的文件路径模式（相对于项目根）
_MEMORY_WORTHY_PATTERNS = [
    "CLAUDE.md",
    "README",
    ".cursorrules",
    ".clinerules",
    "AGENTS.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
]

# 值得记忆的内容关键词
_MEMORY_WORTHY_TERMS = ["偏好", "preference", "规则", "rule", "习惯", "habit"]


def _is_memory_worthy(tool_input: dict) -> bool:
    """判断工具调用的内容是否值得存入记忆"""
    # 检查文件路径
    file_path = tool_input.get("file_path", "")
    for pattern in _MEMORY_WORTHY_PATTERNS:
        if pattern in file_path:
            return True

    # 检查内容是否包含值得记忆的关键词
    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    for term in _MEMORY_WORTHY_TERMS:
        if term.lower() in content.lower():
            return True

    return False


def main():
    """读取钩子事件 JSON，判断是否自动存储记忆"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_input = event.get("tool_input", {})
    if not _is_memory_worthy(tool_input):
        return

    content = tool_input.get("content", "") or tool_input.get("new_string", "")
    file_path = tool_input.get("file_path", "unknown")

    if not content or len(content) < 10:
        return

    plugin = BasePlugin()
    try:
        plugin.auto_store(
            content=f"[{file_path}] {content[:500]}",
            category="project",
            tags=["auto-captured", "claude-code"],
        )
    except Exception:
        pass  # 存储失败不影响主流程
    finally:
        plugin.close()


if __name__ == "__main__":
    main()
