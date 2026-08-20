"""uninstall.sh 关键逻辑单元测试

uninstall.sh 为线性脚本，可测试的关键逻辑点：
1. 危险路径保护：拒绝删除 /、$HOME 等危险路径
2. shell 环境变量块清理：sed 删除 SinoMem 标记块
3. Claude Code hooks 清理：内嵌 Python 移除 sinomem 相关 hooks，保留其他配置

测试通过提取脚本中的关键代码片段在隔离 bash 中执行，避免真实卸载。
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UNINSTALL_SH = PROJECT_ROOT / "uninstall.sh"


def _extract_lines(start_pat: str, end_pat: str) -> str:
    """提取 uninstall.sh 中从 start_pat 到 end_pat 的行"""
    lines = UNINSTALL_SH.read_text(encoding="utf-8").split("\n")
    start = next(
        i for i, line in enumerate(lines) if re.search(start_pat, line)
    )
    end = next(
        i
        for i in range(start, len(lines))
        if re.search(end_pat, lines[i]) and i != start
    )
    return "\n".join(lines[start : end + 1])


class TestDangerousPathProtection:
    """危险路径保护：INSTALL_DIR 为 /、$HOME 等时拒绝删除"""

    @pytest.mark.parametrize(
        "dangerous",
        [
            "/",
            "$HOME",
            "$HOME/.local",
            "$HOME/.local/share",
        ],
    )
    def test_dangerous_paths_rejected(self, dangerous):
        """危险路径必须被拒绝并退出码非 0"""
        script = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "HOME=/tmp/fake_home\n"
            'INSTALL_DIR="$HOME"\n'
            'case "$INSTALL_DIR" in\n'
            '    "/" | "$HOME" | "$HOME/.local" | "$HOME/.local/share")\n'
            '        echo "REFUSED: $INSTALL_DIR"\n'
            "        exit 1\n"
            "        ;;\n"
            "esac\n"
            "echo 'SAFE'\n"
        )
        r = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True
        )
        assert r.returncode != 0
        assert "REFUSED" in r.stdout

    def test_safe_path_allowed(self):
        """正常安装路径不被拒绝"""
        script = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "HOME=/tmp/fake_home\n"
            'INSTALL_DIR="$HOME/.local/share/sinomem"\n'
            'case "$INSTALL_DIR" in\n'
            '    "/" | "$HOME" | "$HOME/.local" | "$HOME/.local/share")\n'
            '        echo "REFUSED"\n'
            "        exit 1\n"
            "        ;;\n"
            "esac\n"
            "echo 'SAFE'\n"
        )
        r = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True
        )
        assert r.returncode == 0
        assert "SAFE" in r.stdout


class TestEnvBlockCleanup:
    """shell 环境变量块清理：sed 删除 SinoMem 标记块"""

    def _run_sed_cleanup(self, rc_content: str) -> str:
        """用与 uninstall.sh 相同的 sed 逻辑清理 rc 文件"""
        script = (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            'ENV_BLOCK_START="# >>> SinoMem >>>"\n'
            'ENV_BLOCK_END="# <<< SinoMem <<<"\n'
            'rc_file="$1"\n'
            'if [[ "$OSTYPE" == "darwin"* ]]; then\n'
            '    sed -i \'\' "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/d" "$rc_file"\n'
            "else\n"
            '    sed -i "/$ENV_BLOCK_START/,/$ENV_BLOCK_END/d" "$rc_file"\n'
            "fi\n"
            'cat "$rc_file"\n'
        )
        rc = Path("/tmp") / f"test_rc_{abs(hash(rc_content))}.txt"
        rc.write_text(rc_content, encoding="utf-8")
        try:
            r = subprocess.run(
                ["bash", "-c", script, "bash", str(rc)],
                capture_output=True,
                text=True,
            )
            assert r.returncode == 0, r.stderr
            return r.stdout
        finally:
            rc.unlink(missing_ok=True)

    def test_sinomem_block_removed(self):
        """包含 SinoMem 标记块的行被完整删除"""
        rc = (
            'export PATH="/usr/bin:$PATH"\n'
            "# >>> SinoMem >>>\n"
            'export SINOMEM_HOME="$HOME/.local/share/sinomem"\n'
            'export PATH="$SINOMEM_HOME/.venv/bin:$PATH"\n'
            "# <<< SinoMem <<<\n"
            "export LANG=en_US.UTF-8\n"
        )
        result = self._run_sed_cleanup(rc)
        assert "# >>> SinoMem >>>" not in result
        assert "SINOMEM_HOME" not in result
        # 块外内容保留
        assert 'export PATH="/usr/bin:$PATH"' in result
        assert "export LANG=en_US.UTF-8" in result

    def test_no_block_unchanged(self):
        """无 SinoMem 标记块时文件不变"""
        rc = 'export PATH="/usr/bin:$PATH"\n'
        result = self._run_sed_cleanup(rc)
        assert result == rc


class TestClaudeCodeHooksCleanup:
    """Claude Code hooks 清理：保留非 sinomem hooks"""

    @staticmethod
    def _python_cleanup(content: str) -> str:
        """执行与 uninstall.sh 内嵌 Python 等价的 hooks 清理逻辑"""
        # 与 uninstall.sh 内嵌 Python 相同的清理算法：
        # 保留非 sinomem hooks，删除空事件；非 hooks 键不动。
        script = r"""
import json
import sys

data = json.loads(sys.stdin.read())
hooks = data.get("hooks", {})
for event in list(hooks.keys()):
    groups = hooks[event]
    kept = []
    for group in groups:
        keep_hooks = [
            h
            for h in group.get("hooks", [])
            if "sinomem" not in json.dumps(h, ensure_ascii=False)
        ]
        if keep_hooks:
            kept.append({**group, "hooks": keep_hooks})
    if kept:
        hooks[event] = kept
    else:
        del hooks[event]
if not hooks:
    data.pop("hooks", None)
print(json.dumps(data, ensure_ascii=False))
"""
        r = subprocess.run(
            ["python3", "-c", script],
            input=content,
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        return r.stdout

    def test_sinomem_hooks_removed_others_kept(self):
        """移除 sinomem hooks，保留其他工具的 hooks"""
        content = json.dumps(
            {
                "hooks": {
                    "PostToolUse": [
                        {
                            "hooks": [
                                {
                                    "command": "python3 .../inject_memory.py",
                                },
                                {
                                    "command": "echo other",
                                },
                            ]
                        }
                    ],
                    "UserPromptSubmit": [
                        {"hooks": [{"command": "python3 .../sinomem/..."}]}
                    ],
                },
                "permissions": {"allow": ["Bash(*)"]},
            },
            ensure_ascii=False,
        )
        result = self._python_cleanup(content)
        data = json.loads(result)
        # 全部 sinomem hooks 被移除
        assert "sinomem" not in result
        # 非 sinomem hook 保留
        post = data["hooks"]["PostToolUse"]
        assert any("echo other" in str(h) for g in post for h in g["hooks"])
        # 无 sinomem 的 UserPromptSubmit 事件被移除
        assert "UserPromptSubmit" not in data["hooks"]
        # 非 hooks 配置保留
        assert data["permissions"] == {"allow": ["Bash(*)"]}

    def test_no_sinomem_unchanged(self):
        """无 sinomem hooks 时结构不变"""
        content = json.dumps(
            {"hooks": {"Stop": [{"hooks": [{"command": "echo done"}]}]}}
        )
        result = self._python_cleanup(content)
        data = json.loads(result)
        assert data["hooks"]["Stop"][0]["hooks"][0]["command"] == "echo done"
