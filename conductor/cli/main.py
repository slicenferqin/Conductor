"""Conductor CLI - Submit tasks, check status, pull results."""

import typer
from rich.console import Console

app = typer.Typer(
    name="conductor",
    help="Async AI development service - submit requirements, get working code.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def submit(
    requirement: str = typer.Argument(..., help="Project requirement description"),
    notify: str = typer.Option("terminal", help="Notification channel: terminal, wechat, feishu"),
) -> None:
    """Submit a new development task."""
    console.print(f"[bold green]Task submitted![/bold green]")
    console.print(f"Requirement: {requirement}")
    console.print(f"Notification: {notify}")
    console.print("\n[yellow]Coming soon...[/yellow]")


@app.command()
def status(
    task_id: str = typer.Argument(..., help="Task ID to check"),
) -> None:
    """Check task status."""
    console.print(f"[bold]Task Status:[/bold] {task_id}")
    console.print("\n[yellow]Coming soon...[/yellow]")


@app.command()
def pull(
    task_id: str = typer.Argument(..., help="Task ID to pull"),
    output: str = typer.Option(".", help="Output directory"),
) -> None:
    """Pull completed task results."""
    console.print(f"[bold]Pulling task:[/bold] {task_id}")
    console.print(f"Output directory: {output}")
    console.print("\n[yellow]Coming soon...[/yellow]")


@app.command()
def server(
    host: str = typer.Option("127.0.0.1", help="Server host"),
    port: int = typer.Option(8000, help="Server port"),
    daemon: bool = typer.Option(False, help="Run as daemon"),
) -> None:
    """Start the Conductor server."""
    console.print(f"[bold green]Starting Conductor server...[/bold green]")
    console.print(f"Host: {host}:{port}")
    console.print(f"Daemon mode: {daemon}")
    console.print("\n[yellow]Coming soon...[/yellow]")


@app.command()
def list_tasks() -> None:
    """List all tasks."""
    console.print("[bold]Task List[/bold]")
    console.print("\n[yellow]Coming soon...[/yellow]")


if __name__ == "__main__":
    app()