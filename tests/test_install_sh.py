"""install.sh 的 set_memory_provider 函数单元测试

通过 subprocess 从 install.sh 提取 set_memory_provider 函数，
在隔离的 bash 环境中执行，验证对 Hermes config.yaml 的修改逻辑：
- 已有 memory 段 + provider → 精确替换（不影响 mcp_servers 等其他段）
- 已有 memory 段但无 provider → 追加 provider
- 无 memory 段 → 追加完整段
- 文件不存在 → 优雅提示
"""

import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTALL_SH = PROJECT_ROOT / "install.sh"


def _extract_func(name: str) -> str:
    """从 install.sh 提取指定函数的完整源码"""
    lines = INSTALL_SH.read_text(encoding="utf-8").split("\n")
    start = next(
        i
        for i, line in enumerate(lines)
        if line.strip().startswith(f"{name}()")
    )
    # 函数闭合 }：顶格且与函数体起始缩进一致（awk 内 { } 均有缩进）
    end = next(i for i in range(start + 1, len(lines)) if lines[i] == "}")
    return "\n".join(lines[start : end + 1])


def _run_function(
    func_code: str, config_content: str
) -> subprocess.CompletedProcess:
    """将函数与一段 config.yaml 组合为临时脚本执行，返回结果"""
    script = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "GREEN=''\nYELLOW=''\nNC=''\nBOLD=''\n"
        + func_code
        + '\n\nset_memory_provider "$1"\n'
        "echo '---CONFIG-START---'\n"
        'cat "$1"\n'
        "echo '---CONFIG-END---'\n"
    )
    cfg_path = Path("/tmp") / f"test_cfg_{abs(hash(config_content))}.yaml"
    cfg_path.write_text(config_content, encoding="utf-8")
    try:
        return subprocess.run(
            ["bash", "-c", script, "bash", str(cfg_path)],
            capture_output=True,
            text=True,
            timeout=10,
        )
    finally:
        cfg_path.unlink(missing_ok=True)


class TestSetMemoryProvider:
    """set_memory_provider 函数行为测试"""

    @pytest.fixture(scope="module")
    def func_code(self):
        """提取一次函数源码供本模块所有用例复用"""
        return _extract_func("set_memory_provider")

    def test_memory_provider_replaced_only_in_memory_section(self, func_code):
        """已有 memory.provider → 精确替换，不影响 mcp_servers 等其他段"""
        config = (
            "memory:\n"
            "  provider: holographic\n"
            "mcp_servers:\n"
            "  foo:\n"
            "    provider: something\n"
        )
        r = _run_function(func_code, config)
        assert r.returncode == 0, r.stderr
        result = r.stdout

        # memory 段 provider 已被替换
        assert "memory:\n  provider: sinomem" in result
        # 其他段 provider 未被误改
        assert "provider: something" in result
        assert "mcp_servers" in result

    def test_memory_section_without_provider_appends(self, func_code):
        """memory 段存在但无 provider → 追加 provider，其他段保留"""
        config = (
            "memory:\n"
            "  ttl: 3600\n"
            "mcp_servers:\n"
            "  bar:\n"
            "    provider: keepme\n"
        )
        r = _run_function(func_code, config)
        assert r.returncode == 0, r.stderr
        result = r.stdout

        # memory 段追加了 provider
        assert "memory:\n  provider: sinomem" in result
        assert "ttl: 3600" in result
        # 其他段 provider 保留
        assert "provider: keepme" in result

    def test_no_memory_section_appends_full_section(self, func_code):
        """无 memory 段 → 追加完整 memory 段"""
        config = "mcp_servers:\n  baz:\n    provider: keepme\n"
        r = _run_function(func_code, config)
        assert r.returncode == 0, r.stderr
        result = r.stdout

        assert "memory:\n  provider: sinomem" in result
        # 原内容保留
        assert "provider: keepme" in result

    def test_multiple_provider_in_mcp_servers_unaffected(self, func_code):
        """mcp_servers 有多个 provider → 全部不被误改"""
        config = (
            "memory:\n"
            "  provider: holographic\n"
            "mcp_servers:\n"
            "  a:\n"
            "    provider: x\n"
            "  b:\n"
            "    provider: y\n"
        )
        r = _run_function(func_code, config)
        assert r.returncode == 0, r.stderr
        result = r.stdout

        # 提取 ---CONFIG-START--- 与 ---CONFIG-END--- 之间的实际文件内容
        config_out = result.split("---CONFIG-START---")[1].split(
            "---CONFIG-END---"
        )[0]
        assert "memory:\n  provider: sinomem" in config_out
        assert "provider: x" in config_out
        assert "provider: y" in config_out
        # 只替换了 1 个 provider（memory 段的）
        assert config_out.count("provider: sinomem") == 1

    def test_missing_config_file_graceful(self, func_code):
        """配置文件不存在 → 不报错，返回成功"""
        script = (
            "#!/usr/bin/env bash\n"
            "GREEN=''\nYELLOW=''\nNC=''\nBOLD=''\n"
            + func_code
            + "\n\nset_memory_provider /tmp/definitely_not_exists.yaml\n"
            "echo 'SCRIPT_DONE'\n"
        )
        r = subprocess.run(
            ["bash", "-c", script], capture_output=True, text=True, timeout=10
        )
        assert r.returncode == 0, r.stderr
        assert "SCRIPT_DONE" in r.stdout
