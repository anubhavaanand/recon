import typer
import asyncio
from typing import Optional
from tui.app import ReconApp
from storage.cache import CacheDatabase
from cli.export import export_records
from core.config import load_config, save_config, Config
from core.search import search_all
from rich.console import Console
from rich.table import Table

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config", help="Manage API keys and settings.")
console = Console()

@app.command()
def search(query: Optional[str] = typer.Argument(None, help="Patent search query (optional - launches TUI if omitted)")):
    """
    Search for patents.
    
    Without a query: launches interactive TUI.
    With a query: performs CLI search and displays results.
    """
    if query is None:
        # Launch interactive TUI mode
        ui = ReconApp()
        ui.run()
    else:
        # CLI search mode
        try:
            console.print(f"[cyan]Searching for: {query}[/cyan]")
            results = asyncio.run(search_all(query))
            
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
            console.print(f"[red]ERR: Search failed. {str(e)}[/red]")
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
    uspto_key: Optional[str] = typer.Option(None, "--uspto-key", help="USPTO API Key"),
    epo_key: Optional[str] = typer.Option(None, "--epo-key", help="EPO Consumer Key"),
    epo_secret: Optional[str] = typer.Option(None, "--epo-secret", help="EPO Consumer Secret"),
):
    """Set API keys for patent sources."""
    config = load_config()
    if uspto_key:
        config.uspto_api_key = uspto_key
    if epo_key:
        config.epo_consumer_key = epo_key
    if epo_secret:
        config.epo_consumer_secret = epo_secret
    
    save_config(config)
    typer.echo("Configuration updated successfully.")

@config_app.command("show")
def config_show():
    """Show current configuration (keys partially hidden)."""
    config = load_config()
    def mask(s):
        return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "****"
    
    typer.echo(f"USPTO API Key: {mask(config.uspto_api_key)}")
    typer.echo(f"EPO Consumer Key: {mask(config.epo_consumer_key)}")
    typer.echo(f"EPO Consumer Secret: {mask(config.epo_consumer_secret)}")

@config_app.command("test")
def config_test():
    """Test configured API keys."""
    from clients.patent_apis import USPTOClient, EPOClient
    import asyncio
    
    async def run_tests():
        console.print("[cyan]Testing API Keys...[/cyan]")
        uspto = USPTOClient()
        epo = EPOClient()
        
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
            
    asyncio.run(run_tests())

if __name__ == "__main__":
    app()
