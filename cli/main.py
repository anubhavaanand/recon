import typer
from tui.app import ReconApp
from storage.cache import CacheDatabase
from cli.export import export_records

app = typer.Typer()

@app.command()
def search():
    """Launch the terminal-native patent research tool."""
    ui = ReconApp()
    ui.run()

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
        typer.echo(f"ERR: Export failed. {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
