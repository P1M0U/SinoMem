"""CLI 命令行工具"""

import json

import click

from .engine import MemoryEngine


@click.group()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--no-embed", is_flag=True, help="禁用嵌入模型（仅 FTS5）")
@click.pass_context
def main(ctx, db_path, no_embed):
    """Agent Memory Lite — 轻量级中文记忆系统"""
    ctx.ensure_object(dict)
    embedder = None
    if not no_embed:
        try:
            from .embedder import Embedder

            embedder = Embedder()
        except Exception:
            pass
    ctx.obj["engine"] = MemoryEngine(db_path, embedder=embedder)


@main.command()
@click.argument("content")
@click.option("-c", "--category", default="general", help="分类")
@click.option("-t", "--tags", default="", help="标签（逗号分隔）")
@click.pass_context
def store(ctx, content, category, tags):
    """存储一条记忆"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    engine = ctx.obj["engine"]
    memory_id = engine.store(content, category, tag_list)
    click.echo(f"ok  id={memory_id}")


@main.command()
@click.argument("query")
@click.option(
    "-m",
    "--mode",
    default="keyword",
    type=click.Choice(["keyword", "semantic", "hybrid"]),
    help="搜索模式",
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
@click.pass_context
def update(ctx, memory_id, content, category, tags):
    """更新记忆"""
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    engine = ctx.obj["engine"]
    ok = engine.update(memory_id, content=content, category=category, tags=tag_list)
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
    """列出记忆"""
    engine = ctx.obj["engine"]
    results = engine.list_memories(category=category, limit=limit)
    if not results:
        click.echo("(empty)")
        return
    for r in results:
        tags_str = f"  [{', '.join(r['tags'])}]" if r.get("tags") else ""
        click.echo(f"#{r['id']}  {r['category']}{tags_str}  {r['created_at']}")
        click.echo(f"  {r['content'][:80]}")
        click.echo()


@main.command()
@click.pass_context
def stats(ctx):
    """查看统计信息"""
    engine = ctx.obj["engine"]
    s = engine.stats()
    click.echo(f"total: {s['total']}")
    for cat, cnt in s["categories"].items():
        click.echo(f"  {cat}: {cnt}")
    if s["vector_enabled"]:
        click.echo(f"vectors: {s['vectors']}")
    else:
        click.echo("vectors: disabled")


@main.command()
@click.option("--db", "db_path", default=None, help="数据库路径")
@click.option("--model-dir", default=None, help="嵌入模型目录")
def migrate(db_path, model_dir):
    """为已有记忆生成向量嵌入"""
    from .migrate import migrate as do_migrate

    # 复用 migrate 命令的逻辑
    import sys

    sys.argv = ["migrate"]
    if db_path:
        sys.argv.extend(["--db", db_path])
    if model_dir:
        sys.argv.extend(["--model-dir", model_dir])
    do_migrate()


@main.command("import")
@click.option("--source", default=None, help="holographic memory_store.db 路径")
@click.option("--db", "db_path", default=None, help="目标数据库路径")
@click.option("--dry-run", is_flag=True, help="仅预览，不实际写入")
def import_memories(source, db_path, dry_run):
    """从 holographic memory 导入记忆"""
    from .import_holographic import import_holographic
    import sys

    args = ["import"]
    if source:
        args.extend(["--source", source])
    if db_path:
        args.extend(["--db", db_path])
    if dry_run:
        args.append("--dry-run")
    sys.argv = args
    import_holographic()


if __name__ == "__main__":
    main()
