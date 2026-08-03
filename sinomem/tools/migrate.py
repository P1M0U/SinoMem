"""数据库迁移脚本 — 为已有记忆批量生成向量"""

import click


def migrate_memories(
    db_path=None, model_dir=None, batch_size=50, force=False
) -> dict:
    """为已有记忆批量生成向量嵌入（纯业务逻辑）

    Args:
        force: True 时重建向量（模型切换场景：维度变化则重建表，
               否则清空旧向量重新生成）

    Returns:
        {"migrated": N, "skipped": N, "total": N, "dim_changed": bool}
    """
    import numpy as np

    from ..core.engine import create_engine

    batch_size = int(batch_size)  # 防御：确保是整数

    engine = create_engine(db_path, model_dir)
    try:
        # 通过公开 API 判断向量是否可用
        stats = engine.stats()
        if not stats.get("vector_enabled"):
            raise RuntimeError("嵌入模型不可用，无法生成向量。请先下载模型。")

        current_dim = engine.embedder_dim
        if current_dim is None:
            raise RuntimeError("嵌入模型不可用，无法生成向量。请先下载模型。")

        existing_dim = engine.get_vec_dim()
        dim_changed = existing_dim is not None and existing_dim != current_dim

        # 维度不匹配时提示用户
        if dim_changed and not force:
            raise RuntimeError(
                f"当前模型维度 ({current_dim}) 与已存向量维度 ({existing_dim}) 不匹配。\n"
                "请使用 --force 强制重建向量，或先删除旧数据库后重新初始化。"
            )

        # --force：维度变化时重建向量表（否则旧维度表写入必失败），
        # 维度相同时仅清空旧向量
        if force and existing_dim is not None:
            if dim_changed:
                engine.recreate_vec_table(current_dim)
                click.echo(
                    f"force: rebuilt vec table "
                    f"(dim {existing_dim} → {current_dim})"
                )
            else:
                cleared = engine.clear_vectors()
                if cleared > 0:
                    click.echo(
                        f"force: cleared {cleared} vectors (dim {current_dim})"
                    )

        memories = engine.list_memories(limit=10**6)
        total = len(memories)

        if total == 0:
            return {
                "migrated": 0,
                "skipped": 0,
                "total": 0,
                "dim_changed": False,
            }

        existing_ids = engine.get_vector_ids()

        # 收集需要迁移的记忆
        pending = [m for m in memories if m["id"] not in existing_ids]

        migrated = 0
        skipped = len(memories) - len(pending)

        # 使用 embed_batch 批量推理，性能远优于逐条 embed
        batch_count = (len(pending) + batch_size - 1) // batch_size
        for bi, i in enumerate(range(0, len(pending), batch_size)):
            batch = pending[i : i + batch_size]
            contents = [m["content"] for m in batch]
            embeddings = engine.embed_batch(contents)

            for mem, embedding in zip(batch, embeddings, strict=True):
                embedding_bytes = np.array(
                    embedding, dtype=np.float32
                ).tobytes()
                engine.add_vector(mem["id"], embedding_bytes)
                migrated += 1

            # 进度提示
            if batch_count > 1:
                click.echo(
                    f"  batch {bi + 1}/{batch_count} "
                    f"({migrated}/{len(pending)})"
                )

        return {
            "migrated": migrated,
            "skipped": skipped,
            "total": total,
            "dim_changed": dim_changed,
        }
    finally:
        engine.close()


@click.command()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--model-dir", default=None, help="嵌入模型目录")
@click.option("--batch-size", default=50, type=int, help="批量大小")
@click.option(
    "--force",
    is_flag=True,
    help="强制重建所有向量（模型切换后使用）",
)
def migrate(db_path, model_dir, batch_size, force):
    """为已有记忆生成向量嵌入（Phase 2 升级）"""
    result = migrate_memories(db_path, model_dir, batch_size, force)
    extra = ""
    if result.get("dim_changed"):
        extra = " (dim changed)"
    click.echo(
        f"done: {result['migrated']} migrated, "
        f"{result['skipped']} skipped, "
        f"{result['total']} total{extra}"
    )


if __name__ == "__main__":
    migrate()
