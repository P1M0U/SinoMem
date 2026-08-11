"""从 holographic memory_store.db 迁移数据到 SinoMem"""

import json
import sqlite3
from pathlib import Path

import click
from loguru import logger

from ..core.engine import MemoryEngine


def import_from_holographic(
    source=None, db_path=None, dry_run=False, no_embed=False
) -> dict:
    """从 holographic memory 导入记忆（纯业务逻辑）

    Returns:
        {"imported": N, "skipped": N, "total": N}

    说明: 上游 trust_score 归一化映射为 importance（0~1）；
    retrieval_count 无对应字段，导入时忽略。
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
    try:
        imported = 0
        skipped = 0

        for f in facts:
            content = f["content"]
            # 跳过空/无效内容：单条脏数据不中断整个导入
            if not content or not str(content).strip():
                skipped += 1
                continue

            # 检查是否已存在（按内容去重，使用 engine 公开 API）
            if engine.exists_by_content(content):
                skipped += 1
                continue

            # 解析 tags（校验为列表，非数组 JSON 回退逗号拆分）
            tags = []
            if f["tags"]:
                try:
                    tags = (
                        json.loads(str(f["tags"]))
                        if str(f["tags"]).startswith("[")
                        else [
                            t.strip()
                            for t in str(f["tags"]).split(",")
                            if t.strip()
                        ]
                    )
                    if not isinstance(tags, list):
                        tags = [
                            t.strip()
                            for t in str(f["tags"]).split(",")
                            if t.strip()
                        ]
                except (json.JSONDecodeError, TypeError):
                    tags = [
                        t.strip()
                        for t in str(f["tags"]).split(",")
                        if t.strip()
                    ]

            # trust_score 归一化映射为 importance（0~1）
            importance = 0.5
            try:
                if f["trust_score"] is not None:
                    importance = max(0.0, min(1.0, float(f["trust_score"])))
            except (TypeError, ValueError):
                pass

            try:
                engine.store(
                    content=content,
                    category=f["category"] or "general",
                    tags=tags,
                    skip_duplicate=False,  # 上游已做去重，跳过重复检查
                    importance=importance,
                )
                imported += 1
            except ValueError as e:
                # 单条失败不中断导入，记录后继续
                skipped += 1
                logger.warning("导入失败，已跳过: {}", e)

        return {"imported": imported, "skipped": skipped, "total": total}
    finally:
        engine.close()


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
