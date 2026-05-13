import typer
from typing import Optional

app = typer.Typer()
config_app = typer.Typer()
app.add_typer(config_app, name="config", help="Manage API keys and settings.")


@app.command()
def search():
    """Launch the terminal-native patent research tool."""
    from recon.tui.app import ReconApp

    ui = ReconApp()
    ui.run()


@app.command()
def export(format: str = typer.Option(..., "--format", "-f", help="Export format: csv, json, bibtex, markdown, pdf")):
    """Export the local patent collection."""
    from recon.storage.cache import CacheDatabase
    from recon.cli.export import export_records

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
    from recon.core.config import load_config, save_config

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
    from recon.core.config import load_config

    config = load_config()

    def mask(s):
        return f"{s[:4]}...{s[-4:]}" if s and len(s) > 8 else "****"

    typer.echo(f"USPTO API Key: {mask(config.uspto_api_key)}")
    typer.echo(f"EPO Consumer Key: {mask(config.epo_consumer_key)}")
    typer.echo(f"EPO Consumer Secret: {mask(config.epo_consumer_secret)}")


__all__ = ["app"]
