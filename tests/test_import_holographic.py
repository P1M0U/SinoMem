"""测试 holographic 导入逻辑"""

import sqlite3

import pytest

from agent_memory_lite.import_holographic import import_from_holographic


@pytest.fixture
def holographic_db(tmp_path):
    """创建模拟的 holographic memory_store.db"""
    src_path = tmp_path / "memory_store.db"
    conn = sqlite3.connect(str(src_path))
    conn.execute(
        """
        CREATE TABLE facts (
            fact_id INTEGER PRIMARY KEY,
            content TEXT,
            category TEXT,
            tags TEXT,
            trust_score REAL DEFAULT 1.0,
            retrieval_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "INSERT INTO facts (fact_id, content, category, tags) VALUES (?, ?, ?, ?)",
        (1, "用户偏好飞书", "user_pref", "[]"),
    )
    conn.execute(
        "INSERT INTO facts (fact_id, content, category, tags) VALUES (?, ?, ?, ?)",
        (2, "服务器在阿里云", "project", '["cloud","ops"]'),
    )
    conn.commit()
    conn.close()
    return src_path


class TestImportHolographic:
    def test_import_dry_run(self, tmp_path, holographic_db):
        """dry_run 不写入，返回正确计数"""
        db_path = str(tmp_path / "target.db")
        result = import_from_holographic(
            source=str(holographic_db), db_path=db_path, dry_run=True
        )
        assert result["total"] == 2
        assert result["imported"] == 0

        # 验证目标数据库未被创建（dry_run 不写入）
        import os

        assert not os.path.exists(db_path)

    def test_import_deduplicates(self, tmp_path, holographic_db):
        """重复内容不重复导入"""
        db_path = str(tmp_path / "target2.db")

        # 第一次导入
        result1 = import_from_holographic(
            source=str(holographic_db), db_path=db_path
        )
        assert result1["imported"] == 2

        # 第二次导入（应全部去重）
        result2 = import_from_holographic(
            source=str(holographic_db), db_path=db_path
        )
        assert result2["imported"] == 0
        assert result2["skipped"] == 2
