"""数据库迁移脚本 — 为已有记忆批量生成向量"""

import click
import numpy as np


def migrate_memories(db_path=None, model_dir=None, batch_size=50) -> dict:
    """为已有记忆批量生成向量嵌入（纯业务逻辑）

    Returns:
        {"migrated": N, "skipped": N, "total": N}
    """
    from ..core.engine import create_engine

    engine = create_engine(db_path, model_dir)

    # 通过公开 API 判断向量是否可用（不访问私有属性）
    stats = engine.stats()
    if not stats.get("vector_enabled"):
        engine.close()
        raise RuntimeError("嵌入模型不可用，无法生成向量。请先下载模型。")

    # embedder 存在时通过 stats 确认后，从内部获取（仅此一处桥接）
    embedder = engine._embedder
    if embedder is None:
        engine.close()
        raise RuntimeError("嵌入模型不可用，无法生成向量。请先下载模型。")

    memories = engine.list_memories(limit=10**6)
    total = len(memories)

    if total == 0:
        engine.close()
        return {"migrated": 0, "skipped": 0, "total": 0}

    existing_ids = engine.get_vector_ids()

    # 收集需要迁移的记忆
    pending = [m for m in memories if m["id"] not in existing_ids]

    migrated = 0
    skipped = len(memories) - len(pending)

    # 使用 embed_batch 批量推理，性能远优于逐条 embed
    for i in range(0, len(pending), batch_size):
        batch = pending[i : i + batch_size]
        contents = [m["content"] for m in batch]
        embeddings = embedder.embed_batch(contents)

        for mem, embedding in zip(batch, embeddings, strict=True):
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            engine.add_vector(mem["id"], embedding_bytes)
            migrated += 1

    engine.close()
    return {"migrated": migrated, "skipped": skipped, "total": total}


@click.command()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--model-dir", default=None, help="嵌入模型目录")
@click.option("--batch-size", default=50, help="批量大小")
def migrate(db_path, model_dir, batch_size):
    """为已有记忆生成向量嵌入（Phase 2 升级）"""
    result = migrate_memories(db_path, model_dir, batch_size)
    click.echo(
        f"done: {result['migrated']} migrated, "
        f"{result['skipped']} skipped, "
        f"{result['total']} total"
    )


if __name__ == "__main__":
    migrate()
