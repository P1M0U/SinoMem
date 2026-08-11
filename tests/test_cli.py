"""CLI 命令测试（使用 --db 指向临时库 + --no-embed 避免模型探测）"""

from click.testing import CliRunner

from sinomem.entrypoints.cli import main


def _invoke(db_path, *args):
    """以指定数据库运行 CLI 子命令"""
    return CliRunner().invoke(main, ["--db", db_path, "--no-embed", *args])


class TestCLI:
    def test_store_and_search(self, tmp_path):
        db = str(tmp_path / "c.db")
        r = _invoke(db, "store", "CLI 测试内容", "-c", "user_pref")
        assert r.exit_code == 0, r.output
        assert "ok" in r.output

        r2 = _invoke(db, "search", "CLI")
        assert r2.exit_code == 0
        assert "CLI 测试内容" in r2.output

    def test_get(self, tmp_path):
        db = str(tmp_path / "c.db")
        _invoke(db, "store", "获取测试")
        r = _invoke(db, "get", "1")
        assert r.exit_code == 0
        assert "获取测试" in r.output

    def test_stats(self, tmp_path):
        db = str(tmp_path / "c.db")
        _invoke(db, "store", "统计测试")
        r = _invoke(db, "stats")
        assert r.exit_code == 0
        assert "total: 1" in r.output

    def test_list_and_delete(self, tmp_path):
        db = str(tmp_path / "c.db")
        _invoke(db, "store", "列表条目")
        r = _invoke(db, "list")
        assert "列表条目" in r.output

        r2 = _invoke(db, "delete", "1")
        assert "ok" in r2.output
        r3 = _invoke(db, "get", "1")
        assert "not found" in r3.output

    def test_clean_requires_force(self, tmp_path):
        """clean 无 --force 仅预览，不实际删除"""
        db = str(tmp_path / "c.db")
        _invoke(db, "store", "待清理")
        r = _invoke(db, "clean")
        assert r.exit_code == 0
        assert "--force" in r.output  # 预览提示

        # 带 --force 才真正清空
        r2 = _invoke(db, "clean", "--force")
        assert "deleted all" in r2.output
        s = _invoke(db, "stats")
        assert "total: 0" in s.output

    def test_search_empty(self, tmp_path):
        db = str(tmp_path / "c.db")
        r = _invoke(db, "search", "不存在的关键词xyz")
        assert r.exit_code == 0
        assert "no results" in r.output
