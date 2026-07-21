"""从 holographic memory_store.db 迁移数据到 SinoMem"""

import json
import sqlite3
from pathlib import Path

import click

from ..core.engine import MemoryEngine


def import_from_holographic(
    source=None, db_path=None, dry_run=False, no_embed=False
) -> dict:
    """从 holographic memory 导入记忆（纯业务逻辑）

    Returns:
        {"imported": N, "skipped": N, "total": N}
    """
    source = (
        Path(source) if source else Path.home() / ".hermes" / "memory_store.db"
    )
    if not source.exists():
        raise FileNotFoundError(f"source not found: {source}")

    src_conn = sqlite3.connect(str(source))
    src_conn.row_factory = sqlite3.Row

    # 读取所有 facts
    facts = src_conn.execute(
        "SELECT fact_id, content, category, tags, trust_score, "
        "retrieval_count, created_at FROM facts ORDER BY fact_id"
    ).fetchall()
    src_conn.close()

    total = len(facts)

    if dry_run:
        return {"imported": 0, "skipped": 0, "total": total}

    # 写入 SinoMem
    if no_embed:
        engine = MemoryEngine(db_path)
    else:
        from ..core.engine import create_engine

        engine = create_engine(db_path)
    imported = 0
    skipped = 0

    for f in facts:
        # 检查是否已存在（按内容去重，使用 engine 公开 API）
        if engine.exists_by_content(f["content"]):
            skipped += 1
            continue

        # 解析 tags
        tags = []
        if f["tags"]:
            try:
                tags = (
                    json.loads(f["tags"])
                    if f["tags"].startswith("[")
                    else [t.strip() for t in f["tags"].split(",") if t.strip()]
                )
            except (json.JSONDecodeError, TypeError):
                tags = [t.strip() for t in f["tags"].split(",") if t.strip()]

        engine.store(
            content=f["content"],
            category=f["category"] or "general",
            tags=tags,
            skip_duplicate=False,  # 上游已做 exists_by_content 去重，跳过重复检查
        )
        imported += 1

    engine.close()
    return {"imported": imported, "skipped": skipped, "total": total}


@click.command()
@click.option(
    "--source", default=None, help="holographic memory_store.db 路径"
)
@click.option("--db", "db_path", default=None, help="SinoMem 数据库路径")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际写入")
def import_holographic(source, db_path, dry_run):
    """从 holographic memory 导入记忆"""
    result = import_from_holographic(source, db_path, dry_run)

    if dry_run:
        click.echo(f"would import {result['total']} facts (dry run)")
        return

    click.echo(
        f"done: {result['imported']} imported, "
        f"{result['skipped']} skipped (duplicates)"
    )


if __name__ == "__main__":
    import_holographic()
