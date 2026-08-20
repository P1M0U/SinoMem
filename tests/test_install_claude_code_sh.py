"""installers/install_claude_code.sh 单元测试

脚本运行时会写入 settings.local.json。测试通过注入临时 HOME 与
临时工作目录隔离，验证：
- hooks JSON 结构与命令路径正确
- 已有配置时合并保留其他键
- --global 模式安装到 $HOME/.claude
"""

import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "installers" / "install_claude_code.sh"

HOOK_EVENTS = {"UserPromptSubmit", "PostToolUse", "Stop"}
HOOK_FILES = {"inject_memory.py", "capture_write.py", "persist_session.py"}


def _run_script(script_args, tmp_path, home_dir, cwd):
    """在隔离环境中运行 install_claude_code.sh"""
    env = {
        "HOME": str(home_dir),
        "PATH": "/usr/bin:/bin:/usr/local/bin",
        "SINOMEM_PYTHON": "python3",  # 避免依赖项目 venv
        "SINOMEM_HOME": str(PROJECT_ROOT),
    }
    return subprocess.run(
        ["bash", str(SCRIPT), *script_args],
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestInstallClaudeCode:
    def test_project_local_mode_creates_hooks(self, tmp_path):
        """项目本地模式：在 cwd/.claude 生成 settings.local.json，含 3 个 hooks"""
        r = _run_script([], tmp_path, tmp_path / "home", tmp_path)
        assert r.returncode == 0, r.stderr

        settings = json.loads(
            (tmp_path / ".claude" / "settings.local.json").read_text()
        )
        assert set(settings["hooks"].keys()) == HOOK_EVENTS

        # 每个 hook 的命令应指向对应插件脚本
        for _event, group in settings["hooks"].items():
            for g in group:
                for h in g["hooks"]:
                    cmd = h["command"]
                    assert cmd.startswith("python3 "), cmd
                    # 应引用 sinomem 插件目录
                    assert "sinomem/plugins/claude_code/" in cmd, cmd

    def test_global_mode_installs_to_home(self, tmp_path):
        """--global 模式：安装到 $HOME/.claude/settings.local.json"""
        home = tmp_path / "home"
        r = _run_script(["--global"], tmp_path, home, tmp_path)
        assert r.returncode == 0, r.stderr

        settings_path = home / ".claude" / "settings.local.json"
        assert settings_path.exists()
        settings = json.loads(settings_path.read_text())
        assert set(settings["hooks"].keys()) == HOOK_EVENTS

    def test_merge_preserves_existing_keys(self, tmp_path):
        """已有 settings.local.json：合并 hooks，保留其他键"""
        cwd = tmp_path
        (cwd / ".claude").mkdir()
        existing = {
            "permissions": {"allow": ["Bash(*):*"]},
            "model": "claude-sonnet-4-5",
        }
        (cwd / ".claude" / "settings.local.json").write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n"
        )

        r = _run_script([], tmp_path, tmp_path / "home", cwd)
        assert r.returncode == 0, r.stderr

        merged = json.loads(
            (cwd / ".claude" / "settings.local.json").read_text()
        )
        # 原有键保留
        assert merged["permissions"] == existing["permissions"]
        assert merged["model"] == existing["model"]
        # hooks 已合并
        assert set(merged["hooks"].keys()) == HOOK_EVENTS

    def test_backup_created_when_config_exists(self, tmp_path):
        """已有配置时生成 .bak 备份"""
        cwd = tmp_path
        (cwd / ".claude").mkdir()
        (cwd / ".claude" / "settings.local.json").write_text("{}")

        r = _run_script([], tmp_path, tmp_path / "home", cwd)
        assert r.returncode == 0, r.stderr
        backups = list((cwd / ".claude").glob("settings.local.json.bak.*"))
        assert len(backups) == 1
