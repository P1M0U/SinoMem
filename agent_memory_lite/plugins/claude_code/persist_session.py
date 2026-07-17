"""Claude Code Stop 钩子 — 会话结束时自动持久化记忆

当 Claude Code 会话结束（用户退出或会话终止），自动将当前会话
中有价值的信息存入长期记忆。

配置方式：运行安装脚本自动配置
    bash installers/install_claude_code.sh
    bash installers/install_claude_code.sh --global   # 全局安装

或手动添加 hooks 到 ~/.claude/settings.local.json 或项目 .claude/settings.local.json:

{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "command": "python3 <项目路径>/agent_memory_lite/plugins/claude_code/persist_session.py"
      }]
    }]
  }
}
"""

import json
import sys
from datetime import UTC, datetime

# 优先从已安装的包导入，回退到 sys.path
try:
    from agent_memory_lite.plugins.base import BasePlugin
except ImportError:
    from pathlib import Path

    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from agent_memory_lite.plugins.base import BasePlugin  # noqa: E402


def main():
    """读取 Stop 事件，记录会话摘要"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # 从事件中提取会话信息
    session_id = event.get("session_id", "unknown")

    # 记录会话结束标记
    plugin = BasePlugin()
    try:
        plugin.auto_store(
            content=(
                f"Claude Code 会话结束 "
                f"(session={session_id[:12]}..., "
                f"time={datetime.now(UTC).isoformat()[:19]}Z)"
            ),
            category="tool",
            tags=["session-end", "claude-code"],
            ttl="90d",
        )
    except Exception:
        pass
    finally:
        plugin.close()


if __name__ == "__main__":
    main()
