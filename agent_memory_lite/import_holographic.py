"""从 holographic memory_store.db 迁移数据到 Agent Memory Lite"""

import json
import sqlite3
from pathlib import Path

import click

from .engine import MemoryEngine


@click.command()
@click.option("--source", default=None, help="holographic memory_store.db 路径")
@click.option("--db", "db_path", default=None, help="Agent Memory Lite 数据库路径")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际写入")
def import_holographic(source, db_path, dry_run):
    """从 holographic memory 导入记忆"""
    source = Path(source) if source else Path.home() / ".hermes" / "memory_store.db"
    if not source.exists():
        click.echo(f"source not found: {source}")
        return

    src_conn = sqlite3.connect(str(source))
    src_conn.row_factory = sqlite3.Row

    # 读取所有 facts
    facts = src_conn.execute(
        "SELECT fact_id, content, category, tags, trust_score, retrieval_count, created_at FROM facts ORDER BY fact_id"
    ).fetchall()
    src_conn.close()

    click.echo(f"found {len(facts)} facts in holographic memory")

    if dry_run:
        for f in facts:
            tags = f["tags"] if f["tags"] else ""
            click.echo(
                f"  #{f['fact_id']} [{f['category']}] trust={f['trust_score']:.2f}"
            )
            click.echo(f"    {f['content'][:80]}")
            click.echo(f"    tags: {tags}")
            click.echo()
        return

    # 写入 Agent Memory Lite
    engine = MemoryEngine(db_path)
    imported = 0
    skipped = 0

    for f in facts:
        # 检查是否已存在（按内容去重）
        existing = engine.conn.execute(
            "SELECT id FROM memories WHERE content = ?", (f["content"],)
        ).fetchone()
        if existing:
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
        )
        imported += 1

    engine.close()
    click.echo(f"done: {imported} imported, {skipped} skipped (duplicates)")


if __name__ == "__main__":
    import_holographic()
