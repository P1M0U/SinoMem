"""数据库迁移脚本 — 为已有记忆批量生成向量"""

import click

from .embedder import Embedder
from .engine import MemoryEngine


@click.command()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--model-dir", default=None, help="嵌入模型目录")
@click.option("--batch-size", default=50, help="批量大小")
def migrate(db_path, model_dir, batch_size):
    """为已有记忆生成向量嵌入（Phase 2 升级）"""
    engine = MemoryEngine(db_path)
    embedder = Embedder(model_dir)

    # 重新初始化 engine 以启用向量
    engine.close()
    engine = MemoryEngine(db_path, embedder=embedder)

    # 获取所有记忆
    rows = engine.conn.execute(
        "SELECT id, content FROM memories ORDER BY id"
    ).fetchall()
    total = len(rows)

    if total == 0:
        click.echo("no memories to migrate")
        return

    click.echo(f"found {total} memories, embedding...")

    # 检查已有向量
    existing_vecs = set()
    if engine._has_vec():
        vec_rows = engine.conn.execute("SELECT id FROM memories_vec").fetchall()
        existing_vecs = {r["id"] for r in vec_rows}

    migrated = 0
    skipped = 0

    for i in range(0, total, batch_size):
        batch = rows[i : i + batch_size]
        for row in batch:
            if row["id"] in existing_vecs:
                skipped += 1
                continue

            embedding = embedder.embed(row["content"])
            import numpy as np

            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            engine.conn.execute(
                "INSERT INTO memories_vec (id, embedding) VALUES (?, ?)",
                (row["id"], embedding_bytes),
            )
            migrated += 1

        engine.conn.commit()
        done = min(i + batch_size, total)
        click.echo(f"  {done}/{total}")

    click.echo(f"done: {migrated} migrated, {skipped} skipped (already had vectors)")
    engine.close()


if __name__ == "__main__":
    migrate()
