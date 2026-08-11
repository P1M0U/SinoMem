"""core 层共享工具 — _row_to_dict 和 update_access

store.py 和 search.py 的共同依赖，抽取到独立模块避免循环引用。
"""

import contextlib
import json
import sqlite3


def _row_to_dict(row, score: float | None = None) -> dict:
    """将 sqlite3.Row 转为 dict，解析 tags JSON"""
    d = dict(row)
    if "tags" in d and d["tags"]:
        with contextlib.suppress(json.JSONDecodeError, TypeError):
            d["tags"] = json.loads(d["tags"])
    if score is not None:
        d["score"] = round(score, 4)
    return d


def update_access(
    conn: sqlite3.Connection, rows: list, commit: bool = True
) -> None:
    """批量更新访问计数（executemany，可延迟提交）

    Args:
        commit: False 时累积不提交，由调用方统一 commit（用于批量搜索，
            避免每个查询单独提交的写放大）

    读路径上的访问计数是尽力而为的元数据：与并发写操作冲突时
    静默跳过（回滚残留事务），不影响搜索主流程。
    """
    if not rows:
        return
    try:
        ids = [(row["id"],) for row in rows]
        conn.executemany(
            "UPDATE memories SET access_count = access_count + 1, "
            "last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
            ids,
        )
        if commit:
            conn.commit()
    except sqlite3.OperationalError:
        # 并发写锁冲突（如与 store/delete 同时发生）：回滚半提交事务，
        # 静默跳过本次计数更新
        with contextlib.suppress(sqlite3.Error):
            conn.rollback()
