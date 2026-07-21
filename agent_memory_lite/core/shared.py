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


def update_access(conn: sqlite3.Connection, rows: list) -> None:
    """批量更新访问计数（executemany，单次 commit）"""
    if not rows:
        return
    ids = [(row["id"],) for row in rows]
    conn.executemany(
        "UPDATE memories SET access_count = access_count + 1, "
        "last_accessed = CURRENT_TIMESTAMP WHERE id = ?",
        ids,
    )
    conn.commit()
