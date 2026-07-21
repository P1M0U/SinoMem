"""Claude Code 自动记忆同步插件

三个钩子脚本：
- inject_memory.py   — UserPromptSubmit: 自动注入记忆上下文
- capture_write.py   — PostToolUse: 自动捕获记忆写入
- persist_session.py — Stop: 会话结束自动持久化

安装方式：
    bash installers/install_claude_code.sh
    bash installers/install_claude_code.sh --global
"""
