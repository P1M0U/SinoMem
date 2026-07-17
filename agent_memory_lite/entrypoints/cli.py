"""CLI 命令行工具（TTL 过期 + 重要性评分）"""

import json

import click

from ..core.engine import MemoryEngine, create_engine


@click.group()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--no-embed", is_flag=True, help="禁用嵌入模型（仅 FTS5）")
@click.pass_context
def main(ctx, db_path, no_embed):
    """Agent Memory Lite — 轻量级中文记忆系统"""
    ctx.ensure_object(dict)
    if no_embed:
        ctx.obj["engine"] = MemoryEngine(db_path)
    else:
        ctx.obj["engine"] = create_engine(db_path)


@main.command()
@click.argument("content")
@click.option("-c", "--category", default="general", help="分类")
@click.option("-t", "--tags", default="", help="标签（逗号分隔）")
@click.option("--allow-duplicate", is_flag=True, help="允许重复存储相同内容")
@click.option(
    "--ttl",
    default=None,
    help="过期时间，如 30d / 24h / 7d12h（None=永不过期）",
)
@click.option(
    "--importance",
    default=0.5,
    type=float,
    help="重要性评分 0.0~1.0（默认 0.5）",
)
@click.pass_context
def store(ctx, content, category, tags, allow_duplicate, ttl, importance):
    """存储一条记忆"""
    tag_list = (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    )
    engine = ctx.obj["engine"]
    memory_id = engine.store(
        content,
        category,
        tag_list,
        skip_duplicate=not allow_duplicate,
        ttl=ttl,
        importance=importance,
    )
    click.echo(f"ok  id={memory_id}")


@main.command()
@click.argument("query")
@click.option(
    "-m",
    "--mode",
    default="keyword",
    type=click.Choice(["keyword", "semantic", "hybrid"]),
    help="搜索模式（keyword: BM25, hybrid: RRF融合）",
)
@click.option("-l", "--limit", default=5, help="返回条数")
@click.pass_context
def search(ctx, query, mode, limit):
    """搜索记忆"""
    engine = ctx.obj["engine"]
    results = engine.search(query, mode=mode, limit=limit)
    if not results:
        click.echo("(no results)")
        return
    for r in results:
        tags_str = f"  [{', '.join(r['tags'])}]" if r.get("tags") else ""
        score_str = f"  score={r['score']}" if "score" in r else ""
        click.echo(f"#{r['id']}  {r['category']}{tags_str}{score_str}")
        click.echo(f"  {r['content']}")
        click.echo()


@main.command()
@click.argument("memory_id", type=int)
@click.pass_context
def get(ctx, memory_id):
    """获取指定记忆"""
    engine = ctx.obj["engine"]
    result = engine.get(memory_id)
    if not result:
        click.echo(f"id={memory_id} not found")
        return
    click.echo(json.dumps(result, ensure_ascii=False, indent=2))


@main.command()
@click.argument("memory_id", type=int)
@click.option("--content", default=None, help="新内容")
@click.option("-c", "--category", default=None, help="新分类")
@click.option("-t", "--tags", default=None, help="新标签（逗号分隔）")
@click.option("--importance", default=None, type=float, help="重要性 0.0~1.0")
@click.option("--ttl", default=None, help="过期时间（30d/24h/7d12h）")
@click.pass_context
def update(ctx, memory_id, content, category, tags, importance, ttl):
    """更新记忆"""
    tag_list = (
        [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    )
    engine = ctx.obj["engine"]
    ok = engine.update(
        memory_id,
        content=content,
        category=category,
        tags=tag_list,
        importance=importance,
        ttl=ttl,
    )
    click.echo("ok" if ok else "not found")


@main.command()
@click.argument("memory_id", type=int)
@click.pass_context
def delete(ctx, memory_id):
    """删除记忆"""
    engine = ctx.obj["engine"]
    ok = engine.delete(memory_id)
    click.echo("ok" if ok else "not found")


@main.command("list")
@click.option("-c", "--category", default=None, help="按分类过滤")
@click.option("-l", "--limit", default=20, help="返回条数")
@click.pass_context
def list_memories(ctx, category, limit):
    """列出记忆（排除过期）"""
    engine = ctx.obj["engine"]
    results = engine.list_memories(category=category, limit=limit)
    if not results:
        click.echo("(empty)")
        return
    for r in results:
        tags_str = f"  [{', '.join(r['tags'])}]" if r.get("tags") else ""
        imp_str = f"  imp={r.get('importance', 0.5):.1f}"
        expire_str = ""
        if r.get("expires_at"):
            expire_str = f"  expires={r['expires_at'][:10]}"
        click.echo(
            f"#{r['id']}  {r['category']}{tags_str}{imp_str}{expire_str}"
            f"  {r['created_at']}"
        )
        click.echo(f"  {r['content'][:80]}")
        click.echo()


@main.command()
@click.pass_context
def stats(ctx):
    """查看统计信息（含过期数）"""
    engine = ctx.obj["engine"]
    s = engine.stats()
    click.echo(f"total: {s['total']}")
    if s.get("expired", 0) > 0:
        click.echo(f"expired: {s['expired']}")
    for cat, cnt in s["categories"].items():
        click.echo(f"  {cat}: {cnt}")
    if s["vector_enabled"]:
        click.echo(f"vectors: {s['vectors']}")
    else:
        click.echo("vectors: disabled")


@main.command()
@click.pass_context
def vacuum(ctx):
    """回收已删除的磁盘空间（VACUUM）"""
    engine = ctx.obj["engine"]
    result = engine.vacuum()
    size_before_kb = result["size_before"] / 1024
    size_after_kb = result["size_after"] / 1024
    freed_kb = result["freed"] / 1024
    click.echo(f"size_before: {size_before_kb:.1f} KB")
    click.echo(f"size_after:  {size_after_kb:.1f} KB")
    click.echo(f"freed:       {freed_kb:.1f} KB")


@main.command()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--model-dir", default=None, help="嵌入模型目录")
@click.option("--batch-size", default=50, help="批量大小")
@click.option(
    "--force",
    is_flag=True,
    help="强制重建所有向量（模型切换后使用）",
)
@click.option("--no-embed", is_flag=True, help="禁用嵌入模型（仅 FTS5）")
def migrate(db_path, model_dir, batch_size, force, no_embed):
    """为已有记忆生成向量嵌入"""
    from ..tools.migrate import migrate_memories

    if no_embed:
        click.echo("错误: --no-embed 与 migrate 互斥（迁移需要嵌入模型）")
        return
    result = migrate_memories(db_path, model_dir, batch_size, force)
    extra = ""
    if result.get("dim_changed"):
        extra = " (dim changed)"
    click.echo(
        f"done: {result['migrated']} migrated, {result['skipped']} skipped"
        f"{extra}"
    )


@main.command("import")
@click.option(
    "--source", default=None, help="holographic memory_store.db 路径"
)
@click.option("--db", "db_path", default=None, help="目标数据库路径")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际写入")
@click.option("--no-embed", is_flag=True, help="禁用嵌入模型（仅 FTS5）")
def import_memories(source, db_path, dry_run, no_embed):
    """从 holographic memory 导入记忆"""
    from ..tools.import_holographic import import_from_holographic

    result = import_from_holographic(
        source, db_path, dry_run, no_embed=no_embed
    )
    if dry_run:
        click.echo(f"would import {result['total']} facts (dry run)")
        return
    click.echo(
        f"done: {result['imported']} imported, {result['skipped']} skipped"
    )


@main.command()
@click.option("-c", "--category", default=None, help="按分类批量删除")
@click.option("--force", is_flag=True, help="确认执行（否则预览）")
@click.pass_context
def clean(ctx, category, force):
    """批量删除记忆（按分类或清空全部）"""
    engine = ctx.obj["engine"]
    if category:
        if not force:
            s = engine.stats()
            cat_count = s["categories"].get(category, 0)
            click.echo(f"would delete {cat_count} memories in '{category}'")
            click.echo("use --force to confirm")
            return
        count = engine.delete_by_category(category)
        click.echo(f"deleted {count} memories in '{category}'")
    else:
        if not force:
            s = engine.stats()
            click.echo(f"would delete all {s['total']} memories")
            click.echo("use --force to confirm")
            return
        count = engine.delete_all()
        click.echo(f"deleted all {count} memories")


@main.command("store-batch")
@click.option(
    "--file",
    "json_file",
    type=click.File("r", encoding="utf-8"),
    required=True,
    help="JSON 文件路径（每行一个 JSON 对象或整个数组）",
)
@click.option("--allow-duplicate", is_flag=True, help="允许重复存储相同内容")
@click.pass_context
def store_batch_cmd(ctx, json_file, allow_duplicate):
    """从 JSON 文件批量导入记忆

    JSON 格式（每行一条或整个数组）：
    [{"content": "...", "category": "tool", "tags": ["a"],
      "ttl": "30d", "importance": 0.8}, ...]
    """
    import json as _json

    raw = json_file.read()
    try:
        data = _json.loads(raw)
        if not isinstance(data, list):
            click.echo("错误: JSON 必须是数组格式 [...]")
            return
    except _json.JSONDecodeError:
        # 尝试按行解析
        data = [
            _json.loads(line)
            for line in raw.strip().splitlines()
            if line.strip()
        ]

    if not data:
        click.echo("(empty)")
        return

    engine = ctx.obj["engine"]
    try:
        ids = engine.store_batch(data, skip_duplicate=not allow_duplicate)
    except ValueError as e:
        click.echo(f"错误: {e}")
        return

    for i, mid in enumerate(ids):
        click.echo(f"[{i + 1}/{len(ids)}] ok  id={mid}")


@main.command("search-batch")
@click.argument("queries", nargs=-1)
@click.option(
    "-m",
    "--mode",
    default="keyword",
    type=click.Choice(["keyword", "semantic", "hybrid"]),
    help="搜索模式",
)
@click.option("-l", "--limit", default=5, help="每个查询返回条数")
@click.pass_context
def search_batch_cmd(ctx, queries, mode, limit):
    """批量搜索多个关键词

    示例: uv run aml search-batch "飞书" "Docker" "Python" -m keyword
    """
    if not queries:
        click.echo("(no queries)")
        return

    engine = ctx.obj["engine"]
    query_list = [{"query": q, "mode": mode, "limit": limit} for q in queries]
    all_results = engine.search_batch(query_list)

    for i, (query, results) in enumerate(
        zip(queries, all_results, strict=True)
    ):
        click.echo(f'─── 查询 {i + 1}: "{query}" ───')
        if not results:
            click.echo("  (no results)")
        for r in results:
            tags_str = f"  [{', '.join(r['tags'])}]" if r.get("tags") else ""
            score_str = f"  score={r['score']}" if "score" in r else ""
            click.echo(f"  #{r['id']}  {r['category']}{tags_str}{score_str}")
            click.echo(f"    {r['content'][:80]}")
        click.echo()


@main.command()
@click.pass_context
def reindex(ctx):
    """重新分词并重建 FTS5 索引（词典更新后使用）"""
    engine = ctx.obj["engine"]
    result = engine.reindex_fts()
    click.echo(f"reindexed: {result['reindexed']} memories")


@main.command()
@click.pass_context
def cleanup(ctx):
    """清理过期记忆"""
    engine = ctx.obj["engine"]
    count = engine.cleanup_expired()
    click.echo(f"cleaned up: {count} expired memories")


if __name__ == "__main__":
    main()
