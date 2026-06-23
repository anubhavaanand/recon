import typer
import asyncio
import contextlib
from pathlib import Path
from typing import Optional
from tui.app import ReconApp
from storage.cache import CacheDatabase
from cli.export import export_records
from core.config import load_config, save_config, Config
from core.search import search_all, ALL_SOURCES
from rich.console import Console
from rich.table import Table

app = typer.Typer()
config_app = typer.Typer()


def _get_source_from_id(patent_id: str) -> str:
    """Infer source prefix from patent ID."""
    if not patent_id:
        return "UNKNOWN"
    prefix = patent_id[:2].upper()
    mapping = {"US": "USPTO", "EP": "EPO", "WO": "WIPO", "JP": "JPO", "CN": "CNIPA"}
    return mapping.get(prefix, "OTHER")

@app.callback(invoke_without_command=True)
def default_behavior(ctx: typer.Context):
    """RECON - Terminal-native patent research tool."""
    if ctx.invoked_subcommand is None:
        ui = ReconApp()
        ui.run()

app.add_typer(config_app, name="config", help="Manage API keys and settings.")
admin_app = typer.Typer()
app.add_typer(admin_app, name="admin", help="Database admin and cache management commands.")
collection_app = typer.Typer()
app.add_typer(collection_app, name="collection", help="Manage saved patent collection.")
console = Console()

@app.command()
def search(
    query: Optional[str] = typer.Argument(None, help="Patent search query (optional - launches TUI if omitted)"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help=f"Comma-separated source filter. Valid: {','.join(ALL_SOURCES)}. Default: all."),
    file: Optional[str] = typer.Option(None, "--file", "-f", help="File containing queries (one per line) for batch search."),
    format: Optional[str] = typer.Option(None, "--format", help="Output format: json or csv (prints to stdout)."),
):
    """
    Search for patents.
    
    Without a query: launches interactive TUI.
    With a query: performs CLI search and displays results.
    Use --file for batch searches from a file.
    Use --format to pipe results as JSON/CSV to stdout.
    """
    if query is None and file is None:
        ui = ReconApp()
        ui.run()
        return

    # Batch search from file
    if file is not None:
        try:
            with open(file, "r") as fh:
                queries = [line.strip() for line in fh if line.strip()]
        except FileNotFoundError:
            console.print(f"[red]ERR: File not found: {file}[/red]")
            raise typer.Exit(code=1)
        except Exception as e:
            console.print(f"[red]ERR: Cannot read file: {e}[/red]")
            raise typer.Exit(code=1)

        all_results: list = []
        for q in queries:
            console.print(f"[cyan]Searching: {q}[/cyan]")
            try:
                batch = asyncio.run(search_all(q, sources=sources))
                all_results.extend(batch)
            except Exception as e:
                console.print(f"[red]ERR: Batch search failed for '{q}': {e}[/red]")

        if not all_results:
            console.print("[yellow]No results found from batch.[/yellow]")
            raise typer.Exit(code=0)

        results = all_results
    else:
        query = query.strip()
        if not query:
            console.print("[red]ERR: Empty search query. Provide a non-empty query string.[/red]")
            raise typer.Exit(code=1)

        sources_list = None
        if source:
            sources_list = [s.strip() for s in source.split(",")]

        console.print(f"[cyan]Searching for: {query}[/cyan]")
        results = asyncio.run(search_all(query, sources=sources_list))

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        raise typer.Exit(code=0)

    # --format flag: pipe to stdout as JSON or CSV
    if format is not None:
        import json as jsonlib
        fmt = format.lower()
        if fmt == "json":
            out = jsonlib.dumps([r.__dict__ if hasattr(r, "__dict__") else str(r) for r in results], indent=2)
            console.print(out)
        elif fmt == "csv":
            import csv, io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["id", "title", "assignee", "filed_date", "source"])
            for r in results:
                writer.writerow([
                    getattr(r, "id", "[?]"),
                    getattr(r, "title", "[?]"),
                    getattr(r, "assignee", "[?]"),
                    r.dates.get("filed", "[?]") if getattr(r, "dates", None) else "[?]",
                    _get_source_from_id(getattr(r, "id", "")),
                ])
            console.print(buf.getvalue())
        else:
            console.print(f"[red]ERR: Unknown format '{format}'. Use json or csv.[/red]")
            raise typer.Exit(code=1)
        return

    # Display results in a table
    table = Table(title=f"Search Results ({len(results)} patents)")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="green")
    table.add_column("Filed", style="magenta")
    table.add_column("Source", style="yellow")

    for record in results[:50]:
        filed_date = record.dates.get("filed", "[?]") if record.dates else "[?]"
        source_name = _get_source_from_id(record.id or "")
        table.add_row(
            record.id or "[?]",
            (record.title or "[?]")[:55],
            filed_date,
            source_name,
        )

    console.print(table)
    console.print(f"\n[green]✓ Displayed {min(50, len(results))} of {len(results)} results[/green]")

    db = CacheDatabase()
    db.save_search_results(query if file is None else file, results)
    for record in results:
        db.save_to_collection(record)
    console.print(f"[blue]ℹ {len(results)} results cached and added to collection. Use 'recon export --format json' to export.[/blue]")


@app.command()
def run(
    query: Optional[str] = typer.Argument(None, help="Patent search query (optional - launches TUI if omitted)"),
    export_format: Optional[str] = typer.Option(None, "--export", "-e", help="Export format after run: json,csv,markdown,pdf"),
    show_table: bool = typer.Option(True, "--table/--no-table", help="Show a results table in the terminal"),
    source: Optional[str] = typer.Option(None, "--source", "-s", help=f"Comma-separated source filter. Valid: {','.join(ALL_SOURCES)}. Default: all."),
):
    """
    Run an end-to-end recon flow: search, cache, add to collection and optionally export.

    When `query` is omitted the interactive TUI is launched. When provided, the CLI runs the search
    pipeline, caches results, and can export the collection automatically.
    """
    if query is None:
        # Launch TUI
        ui = ReconApp()
        ui.run()
        return

    try:
        query = query.strip()
        if not query:
            console.print("[red]ERR: Empty search query. Provide a non-empty query string.[/red]")
            raise typer.Exit(code=1)

        sources = None
        if source:
            sources = [s.strip() for s in source.split(",")]

        console.print(f"[cyan]Running recon for: {query}[/cyan]")
        results = asyncio.run(search_all(query, sources=sources))

        if not results:
            console.print("[yellow]No results found for run.[/yellow]")
            raise typer.Exit(code=0)

        # Cache and add to collection
        db = CacheDatabase()
        db.save_search_results(query, results)
        for rec in results:
            db.save_to_collection(rec)

        console.print(f"[green]✓ Run complete: {len(results)} records cached and added to collection[/green]")

        if show_table:
            table = Table(title=f"Run Results ({len(results)} patents)")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Title", style="green")
            table.add_column("Filed", style="magenta")
            table.add_column("Source", style="yellow")
            for record in results[:50]:
                filed_date = record.dates.get("filed", "[?]") if getattr(record, "dates", None) else "[?]"
                table.add_row(
                    record.id or "[?]",
                    (record.title or "[?]")[:55],
                    filed_date,
                    _get_source_from_id(record.id or ""),
                )
            console.print(table)

        if export_format:
            output_path = f"collection_export.{export_format}"
            try:
                export_records(db.get_collection(), export_format, output_path)
                console.print(f"[green]✓ Exported collection to {output_path}[/green]")
            except Exception as e:
                console.print(f"[red]ERR: Export failed: {e}[/red]")
                raise typer.Exit(code=1)

    except Exception as e:
        console.print(f"[red]ERR: Run failed. Reason: {str(e)}[/red]")
        raise typer.Exit(code=1)

@app.command()
def export(
    format: str = typer.Option(..., "--format", "-f", help="Export format: csv, json, bibtex, markdown, pdf"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output file path."),
):
    """Export the local patent collection."""
    db = CacheDatabase()
    records = db.get_collection()
    
    if not records:
        typer.echo("ERR: Collection is empty. Save patents with 's' first.")
        raise typer.Exit(code=1)

    output_path = output if output else f"collection_export.{format.lower()}"
    try:
        export_records(records, format, output_path)
        typer.echo(f"Successfully exported {len(records)} records to {output_path}")
    except Exception as e:
        typer.echo("ERR: Export failed. " + str(e))
        raise typer.Exit(code=1)

@config_app.command("set")
def config_set(
    uspto_key: Optional[str] = typer.Option(None, "--uspto-key", help="USPTO API Key (Insecure: use interactive mode instead)"),
    epo_key: Optional[str] = typer.Option(None, "--epo-key", help="EPO Consumer Key (Insecure)"),
    epo_secret: Optional[str] = typer.Option(None, "--epo-secret", help="EPO Consumer Secret (Insecure)"),
    lens_key: Optional[str] = typer.Option(None, "--lens-key", help="Lens API Key (Insecure)"),
    patsnap_key: Optional[str] = typer.Option(None, "--patsnap-key", help="PatSnap API Key (Insecure)"),
    nim_key: Optional[str] = typer.Option(None, "--nim-key", help="NVIDIA NIM API Key (Insecure)"),
):
    """Set API keys for patent sources and AI services."""
    config = load_config()
    
    # If any keys are provided via CLI, update them and warn the user
    if any([uspto_key, epo_key, epo_secret, lens_key, patsnap_key, nim_key]):
        flags_str = ", ".join(
            f"--{k}" for k, v in [("uspto-key", uspto_key), ("epo-key", epo_key), ("epo-secret", epo_secret), ("lens-key", lens_key), ("patsnap-key", patsnap_key), ("nim-key", nim_key)] if v
        )
        console.print(f"[red]WARNING: Providing API keys via CLI arguments is insecure. They may be leaked in shell history or process lists.[/red]")
        if uspto_key: config.uspto_api_key = uspto_key
        if epo_key: config.epo_consumer_key = epo_key
        if epo_secret: config.epo_consumer_secret = epo_secret
        if lens_key: config.lens_api_key = lens_key
        if patsnap_key: config.patsnap_api_key = patsnap_key
        if nim_key: config.nvidia_nim_api_key = nim_key
    else:
        # Fallback to secure interactive mode
        console.print("[yellow]Enter your API keys (leave blank to keep current):[/yellow]")
        
        uspto = typer.prompt("USPTO API Key", default=config.uspto_api_key or "", hide_input=True, show_default=False)
        if uspto: config.uspto_api_key = uspto
            
        epo_k = typer.prompt("EPO Consumer Key", default=config.epo_consumer_key or "", hide_input=True, show_default=False)
        if epo_k: config.epo_consumer_key = epo_k
            
        epo_s = typer.prompt("EPO Consumer Secret", default=config.epo_consumer_secret or "", hide_input=True, show_default=False)
        if epo_s: config.epo_consumer_secret = epo_s
            
        lens = typer.prompt("Lens API Key", default=config.lens_api_key or "", hide_input=True, show_default=False)
        if lens: config.lens_api_key = lens

        patsnap = typer.prompt("PatSnap API Key", default=config.patsnap_api_key or "", hide_input=True, show_default=False)
        if patsnap: config.patsnap_api_key = patsnap

        nim = typer.prompt("NVIDIA NIM API Key", default=config.nvidia_nim_api_key or "", hide_input=True, show_default=False)
        if nim: config.nvidia_nim_api_key = nim
    
    save_config(config)
    typer.echo("Configuration updated successfully and secured (chmod 600).")

@config_app.command("show")
def config_show():
    """Show current configuration (keys partially hidden)."""
    config = load_config()
    def mask(s):
        return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "****"
    
    typer.echo(f"USPTO API Key: {mask(config.uspto_api_key)}")
    typer.echo(f"EPO Consumer Key: {mask(config.epo_consumer_key)}")
    typer.echo(f"EPO Consumer Secret: {mask(config.epo_consumer_secret)}")
    typer.echo(f"Lens API Key: {mask(config.lens_api_key)}")
    typer.echo(f"PatSnap API Key: {mask(config.patsnap_api_key)}")
    typer.echo(f"NVIDIA NIM API Key: {mask(config.nvidia_nim_api_key)}")
    typer.echo(f"Semantic Search: {'enabled' if config.semantic_search_enabled else 'disabled'}")
    typer.echo(f"AI Translation: {'enabled' if config.ai_translation_enabled else 'disabled'}")

@config_app.command("test")
def config_test():
    """Test configured API keys."""
    from clients.patent_apis import USPTOClient, EPOClient, LensClient, PatsnapClient
    import asyncio
    
    async def run_tests():
        console.print("[cyan]Testing API Keys...[/cyan]")
        uspto = USPTOClient()
        epo = EPOClient()
        lens = LensClient()
        patsnap = PatsnapClient()
        
        uspto_ok, uspto_msg = await uspto.validate_credentials()
        if uspto_ok:
            console.print(f"[green]✓ {uspto_msg}[/green]")
        else:
            console.print(f"[red]✗ {uspto_msg}[/red]")
            
        epo_ok, epo_msg = await epo.validate_credentials()
        if epo_ok:
            console.print(f"[green]✓ {epo_msg}[/green]")
        else:
            console.print(f"[red]✗ {epo_msg}[/red]")
            
        lens_ok, lens_msg = await lens.validate_credentials()
        if lens_ok:
            console.print(f"[green]✓ {lens_msg}[/green]")
        else:
            console.print(f"[red]✗ {lens_msg}[/red]")

        patsnap_ok, patsnap_msg = await patsnap.validate_credentials()
        if patsnap_ok:
            console.print(f"[green]✓ {patsnap_msg}[/green]")
        else:
            console.print(f"[red]✗ {patsnap_msg}[/red]")
            
    asyncio.run(run_tests())

# ── Admin commands ─────────────────────────────────────────

@admin_app.command("stats")
def admin_stats():
    """Print cache health and row counts for all tables."""
    db = CacheDatabase()
    health = db.record_cache_health()
    table = Table(title="Cache Health")
    table.add_column("Table", style="cyan")
    table.add_column("Row Count", style="green")
    table.add_column("Corrupt", style="red")
    table.add_column("Expired", style="yellow")
    for entry in health.get("tables", []):
        table.add_row(
            entry["table"],
            str(entry.get("row_count", "?")),
            str(entry.get("corrupt", "?")),
            str(entry.get("expired_rows", "?")),
        )
    console.print(table)
    if "db_size_mb" in health:
        console.print(f"\nDB size: {health['db_size_mb']:.1f} MB")
    if "avg_query_time_ms" in health:
        console.print(f"Avg query time: {health['avg_query_time_ms']:.1f} ms")


@admin_app.command("cache-stats")
def admin_cache_stats():
    """Show detailed cache statistics: hit counts, size, eviction metrics."""
    db = CacheDatabase()
    with contextlib.closing(db.get_connection()) as conn:
        total = conn.execute("SELECT COUNT(*) FROM search_results").fetchone()[0]
        expired = conn.execute("SELECT COUNT(*) FROM search_results WHERE expires_at < CURRENT_TIMESTAMP").fetchone()[0]
        hits = conn.execute("SELECT COALESCE(SUM(hit_count), 0) FROM search_results").fetchone()[0]
        top = conn.execute(
            "SELECT query_text, hit_count, last_accessed FROM search_results ORDER BY hit_count DESC LIMIT 5"
        ).fetchall()

    size_mb = Path(db.db_path).stat().st_size / (1024 * 1024)

    console.print("[bold]Cache Stats[/bold]")
    console.print(f"  Total entries:     {total}")
    console.print(f"  Expired entries:   {expired}")
    console.print(f"  Total hit count:   {hits}")
    console.print(f"  DB size:           {size_mb:.1f} MB")

    if top:
        console.print("\n[bold]Top 5 most accessed:[/bold]")
        for row in top:
            console.print(f"  {row['query_text'][:60]:60s}  hits={row['hit_count']}  last={row['last_accessed'] or 'never'}")

    eviction = db.enforce_eviction_policy()
    console.print(f"\n[bold]Eviction (dry run):[/bold]")
    console.print(f"  Expired deleted:   {eviction['deleted_expired']}")
    console.print(f"  LRU deleted:       {eviction['deleted_lru']}")
    console.print(f"  Old history:       {eviction['deleted_history']}")


@admin_app.command("cache-clear")
def admin_cache_clear(
    older_than: int = typer.Option(30, "--older-than", help="Delete cached results older than N days."),
):
    """Remove old cached search results."""
    from datetime import datetime, timedelta
    db = CacheDatabase()
    cutoff = (datetime.utcnow() - timedelta(days=older_than)).isoformat()
    with db.get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM search_results WHERE last_accessed < ?",
            (cutoff,),
        )
        conn.commit()
        deleted = cursor.rowcount
    console.print(f"[green]Deleted {deleted} cached results older than {older_than} days.[/green]")


@admin_app.command("diagnostics")
def admin_diagnostics(
    api_ping: bool = typer.Option(False, "--api-ping", help="Ping all configured APIs and show latency."),
):
    """Show source health: circuit breaker status, error counts, rate limits."""
    from core.metrics import MetricsCollector, VERSION, SESSION_ID

    db = CacheDatabase()
    sources = db.get_all_source_health()

    if not sources:
        console.print("[yellow]No source metadata recorded. Run a search first to populate.[/yellow]")
    else:
        table = Table(title="Source Health")
        table.add_column("Source", style="cyan")
        table.add_column("Auth", style="magenta")
        table.add_column("Rate Limit", style="yellow")
        table.add_column("Req/hr", style="green")
        table.add_column("Errors", style="red")
        table.add_column("Last Error", style="red")
        table.add_column("Circuit", style="bold")

        for s in sources:
            circuit_status = "[red]OPEN[/red]" if s["circuit_open"] else "[green]CLOSED[/green]"
            last_err = s["last_error_code"] or "—"
            last_err_time = (s["last_error_at"] or "")[:19] if s.get("last_error_at") else "—"
            table.add_row(
                s["source_name"],
                s["auth_type"] or "—",
                str(s["rate_limit_per_minute"] or "—"),
                str(s["requests_this_hour"] or "0"),
                str(s["consecutive_errors"] or "0"),
                f"{last_err} @ {last_err_time}",
                circuit_status,
            )

        console.print(table)
        console.print("\n[dim]Sources with OPEN circuits are skipped during searches.[/dim]")

    if api_ping:
        import asyncio
        import httpx

        console.print("\n[cyan]API Ping Results:[/cyan]")
        targets = {
            "USPTO": "https://api.uspto.gov/api/v1/",
            "WIPO": "https://patentscope.wipo.int",
            "EPO": "https://ops.epo.org",
            "Lens": "https://api.lens.org",
        }

        async def _ping(name: str, url: str) -> tuple[str, float | str]:
            try:
                start = time.time()
                async with httpx.AsyncClient(timeout=5.0) as c:
                    await c.get(url)
                return name, (time.time() - start) * 1000
            except Exception as e:
                return name, str(e)

        async def _run_pings():
            results = await asyncio.gather(
                *[_ping(n, u) for n, u in targets.items()], return_exceptions=True
            )
            for res in results:
                if isinstance(res, tuple):
                    name, latency = res
                    if isinstance(latency, (int, float)):
                        console.print(f"  [green]{name}: {latency:.0f}ms[/green]")
                    else:
                        console.print(f"  [red]{name}: {latency}[/red]")

        asyncio.run(_run_pings())


@admin_app.command("migrate")
def admin_migrate():
    """Run pending database migrations."""
    from storage.migrate import migrate as run_migrations, validate
    db = CacheDatabase()
    applied = run_migrations(db.db_path)
    if applied:
        console.print(f"[green]Applied migrations: {', '.join(applied)}[/green]")
    else:
        console.print("[green]Database already up to date.[/green]")
    missing = validate(db.db_path)
    if missing:
        console.print(f"[red]Missing tables: {', '.join(missing)}[/red]")
    else:
        console.print("[green]All tables present.[/green]")


@admin_app.command("cache-vacuum")
def admin_cache_vacuum():
    """Run SQLite VACUUM to reclaim disk space."""
    db = CacheDatabase()
    result = db.vacuum()
    freed_mb = result["freed_bytes"] / 1024 / 1024
    before_mb = result["before_bytes"] / 1024 / 1024
    after_mb = result["after_bytes"] / 1024 / 1024
    console.print(f"[green]VACUUM complete: {before_mb:.1f} MB → {after_mb:.1f} MB (freed {freed_mb:.1f} MB)[/green]")


@collection_app.command("list")
def collection_list():
    """List all patents in the saved collection."""
    db = CacheDatabase()
    records = db.get_collection()
    if not records:
        console.print("[yellow]Collection is empty.[/yellow]")
        return

    table = Table(title=f"Saved Collection ({len(records)} patents)")
    table.add_column("#", style="dim")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="green")
    table.add_column("Source", style="yellow")
    table.add_column("Filed", style="magenta")

    for i, r in enumerate(records, 1):
        table.add_row(
            str(i),
            r.id or "[?]",
            (r.title or "[?]")[:55],
            _get_source_from_id(r.id or ""),
            r.dates.get("filed", "[?]"),
        )
    console.print(table)

@collection_app.command("clear")
def collection_clear():
    """Remove all patents from the saved collection."""
    db = CacheDatabase()
    count = db.collection_count()
    if count == 0:
        console.print("[yellow]Collection is already empty.[/yellow]")
        return
    db.clear_collection()
    console.print(f"[green]Cleared {count} patents from collection.[/green]")

if __name__ == "__main__":
    app()
