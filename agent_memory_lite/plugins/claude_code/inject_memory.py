"""Claude Code UserPromptSubmit 钩子 — 自动注入记忆上下文

用户在 Claude Code 中输入 prompt 时，自动检索相关记忆并注入到 prompt 末尾。
Agent 完全无感 —— 它看到的是已经增强过的 prompt。

配置方式：运行安装脚本自动配置
    bash installers/install_claude_code.sh
    bash installers/install_claude_code.sh --global   # 全局安装

或手动添加 hooks 到 ~/.claude/settings.local.json 或项目 .claude/settings.local.json:

{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "command": "python3 <项目路径>/agent_memory_lite/plugins/claude_code/inject_memory.py"
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


def main():
    """读取 stdin 的钩子事件 JSON，检索相关记忆并注入到 prompt"""
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        # 无法读取事件视为无操作
        print("", end="")
        return

    # 提取用户输入的 prompt
    prompt = event.get("prompt", "")
    if not prompt or len(prompt) < 3:
        print("", end="")
        return

    plugin = BasePlugin()
    try:
        enhanced = plugin.inject_context(
            current_prompt=prompt,
            mode="hybrid",
            limit=3,
        )
        # 返回增强后的 prompt（Claude Code 会替换原 prompt）
        print(enhanced, end="")
    except Exception:
        # 检索失败不影响主流程，返回原始 prompt
        print(prompt, end="")
    finally:
        plugin.close()


if __name__ == "__main__":
    main()
