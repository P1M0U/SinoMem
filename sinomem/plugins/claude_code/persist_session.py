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
        "command": "python3 <项目路径>/sinomem/plugins/claude_code/persist_session.py"
      }]
    }]
  }
}
"""

import json
import sys

# 优先从已安装的包导入，回退到 sys.path
try:
    from sinomem.plugins.base import BasePlugin
except ImportError:
    from pathlib import Path

    _PROJECT_ROOT = Path(__file__).resolve().parents[3]
    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))
    from sinomem.plugins.base import BasePlugin  # noqa: E402


def main():
    """读取 Stop 事件，记录会话摘要"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # 从事件中提取会话摘要（有真实内容才写入，
    # 避免每会话写入无价值的占位记录污染记忆库）
    summary = event.get("summary", "") or event.get("result", "")
    if not summary or len(summary) < 10:
        return

    # 钩子低频触发但保持轻量，禁用嵌入模型
    plugin = BasePlugin(use_embedder=False)
    try:
        plugin.auto_store(
            content=f"Claude Code 会话结束摘要: {summary[:500]}",
            category="tool",
            tags=["session-end", "claude-code"],
            ttl="90d",
        )
    except Exception as e:
        # 存储失败不影响主流程，但输出到 stderr 便于排查
        print(f"[sinomem] persist_session 存储失败: {e}", file=sys.stderr)
    finally:
        plugin.close()


if __name__ == "__main__":
    main()
