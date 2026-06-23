import typer
import asyncio
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
):
    """
    Search for patents.
    
    Without a query: launches interactive TUI.
    With a query: performs CLI search and displays results.
    """
    if query is None:
        # Launch interactive TUI mode
        print("DEBUG: Launching ReconApp TUI...")
        ui = ReconApp()
        ui.run()
        return

    query = query.strip()
    if not query:
        console.print("[red]ERR: Empty search query. Provide a non-empty query string.[/red]")
        raise typer.Exit(code=1)

    sources = None
    if source:
        sources = [s.strip() for s in source.split(",")]

    try:
        console.print(f"[cyan]Searching for: {query}[/cyan]")
        results = asyncio.run(search_all(query, sources=sources))
        
        if not results:
            console.print("[yellow]No results found.[/yellow]")
            raise typer.Exit(code=0)
        
        # Display results in a table
        table = Table(title=f"Search Results ({len(results)} patents)")
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Title", style="green")
        table.add_column("Filed", style="magenta")
        table.add_column("Assignee", style="yellow")
        
        for record in results[:50]:  # Limit to 50 results for display
            filed_date = record.dates.get("filed", "[?]") if record.dates else "[?]"
            table.add_row(
                record.id or "[?]",
                (record.title or "[?]")[:55],
                filed_date,
                (record.assignee or "[?]")[:35]
            )
        
        console.print(table)
        console.print(f"\n[green]✓ Displayed {min(50, len(results))} of {len(results)} results[/green]")
        
        # Cache search results and add to collection for export
        if len(results) > 0:
            db = CacheDatabase()
            db.save_search_results(query, results)
            # Add all results to collection so they can be exported
            for record in results:
                db.save_to_collection(record)
            console.print(f"[blue]ℹ {len(results)} results cached and added to collection. Use 'recon export --format json' to export.[/blue]")
            
    except Exception as e:
        console.print(f"[red]ERR: Search operation terminated. Reason: {str(e)}[/red]")
        console.print("[yellow]Action: Verify API connectivity and check 'recon config show' for valid keys.[/yellow]")
        raise typer.Exit(code=1)


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
            table.add_column("Assignee", style="yellow")
            for record in results[:50]:
                filed_date = record.dates.get("filed", "[?]") if getattr(record, "dates", None) else "[?]"
                table.add_row(record.id or "[?]", (record.title or "[?]")[:55], filed_date, (record.assignee or "[?]")[:35])
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
def export(format: str = typer.Option(..., "--format", "-f", help="Export format: csv, json, bibtex, markdown, pdf")):
    """Export the local patent collection."""
    db = CacheDatabase()
    records = db.get_collection()
    
    if not records:
        typer.echo("ERR: Collection is empty. No records to export.")
        raise typer.Exit(code=1)
        
    output_path = f"collection_export.{format.lower()}"
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
):
    """Set API keys for patent sources."""
    config = load_config()
    
    # If any keys are provided via CLI, update them and warn the user
    if any([uspto_key, epo_key, epo_secret, lens_key, patsnap_key]):
        console.print("[red]WARNING: Providing API keys via CLI arguments is insecure. They may be leaked in shell history or process lists.[/red]")
        if uspto_key: config.uspto_api_key = uspto_key
        if epo_key: config.epo_consumer_key = epo_key
        if epo_secret: config.epo_consumer_secret = epo_secret
        if lens_key: config.lens_api_key = lens_key
        if patsnap_key: config.patsnap_api_key = patsnap_key
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
    table.add_column("Assignee", style="yellow")
    table.add_column("Filed", style="magenta")

    for i, r in enumerate(records, 1):
        table.add_row(
            str(i),
            r.id or "[?]",
            (r.title or "[?]")[:55],
            (r.assignee or "[?]")[:35],
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
