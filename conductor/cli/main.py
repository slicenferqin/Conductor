"""Conductor CLI - Submit tasks, check status, pull results."""

import asyncio
from datetime import datetime
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from conductor.config import get_config
from conductor.core.decomposer import TaskDecomposer
from conductor.core.executor import TaskExecutor, ExecutionProgress, StageStatus

app = typer.Typer(
    name="conductor",
    help="Async AI development service - submit requirements, get working code.",
    no_args_is_help=True,
)
console = Console()


def _progress_callback(progress: ExecutionProgress) -> None:
    """Handle progress updates from executor."""
    status_emoji = {
        StageStatus.PENDING: "⏳",
        StageStatus.RUNNING: "🔄",
        StageStatus.TESTING: "🧪",
        StageStatus.FIXING: "🔧",
        StageStatus.COMPLETED: "✅",
        StageStatus.FAILED: "❌",
    }
    emoji = status_emoji.get(progress.status, "❓")
    console.print(f"{emoji} {progress.format_for_display()}")


@app.command()
def submit(
    requirement: str = typer.Argument(..., help="Project requirement description"),
    workspace: str = typer.Option(None, help="Project workspace directory"),
    notify: str = typer.Option("terminal", help="Notification channel: terminal, wechat, feishu"),
    yes: bool = typer.Option(False, "-y", "--yes", help="Skip plan confirmation"),
) -> None:
    """Submit a new development task."""
    config = get_config()

    # Create workspace
    if workspace:
        workspace_path = Path(workspace)
    else:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        workspace_path = config.workspace / f"task-{timestamp}"

    workspace_path.mkdir(parents=True, exist_ok=True)

    console.print(Panel(
        f"[bold]需求:[/bold] {requirement}\n[bold]工作目录:[/bold] {workspace_path}",
        title="📋 新任务",
        border_style="blue",
    ))

    # Generate plan
    console.print("\n[bold cyan]正在分析需求，生成开发计划...[/bold cyan]\n")

    try:
        plan = asyncio.run(_generate_plan(str(workspace_path), requirement))
    except Exception as e:
        console.print(f"[bold red]计划生成失败:[/bold red] {e}")
        raise typer.Exit(1)

    # Display plan
    console.print(plan.format_for_display())

    # Confirm plan
    if not yes:
        if not Confirm.ask("[bold yellow]确认执行此计划?[/bold yellow]"):
            console.print("[yellow]已取消[/yellow]")
            raise typer.Exit(0)

    # Execute plan
    console.print("\n[bold green]开始执行...[/bold green]\n")

    try:
        results = asyncio.run(_execute_plan(str(workspace_path), plan))
    except Exception as e:
        console.print(f"[bold red]执行失败:[/bold red] {e}")
        raise typer.Exit(1)

    # Show results
    console.print("\n" + "━" * 50)
    console.print("[bold]执行结果:[/bold]\n")

    all_passed = True
    for result in results:
        if result.status == StageStatus.COMPLETED:
            console.print(f"  ✅ {result.stage_name} - 完成 (修复次数: {result.fix_attempts})")
        else:
            console.print(f"  ❌ {result.stage_name} - 失败")
            if result.error:
                console.print(f"     错误: {result.error[:200]}...")
            all_passed = False

    console.print("━" * 50)

    if all_passed:
        console.print(f"\n[bold green]🎉 任务完成![/bold green]")
        console.print(f"项目位置: {workspace_path}")
        console.print(f"\n启动项目:")
        console.print(f"  cd {workspace_path}")
        console.print(f"  docker-compose up")
    else:
        console.print(f"\n[bold red]任务执行有失败[/bold red]")
        console.print(f"请检查 {workspace_path} 中的代码")


async def _generate_plan(workspace: str, requirement: str):
    """Generate development plan."""
    decomposer = TaskDecomposer(workspace)
    return await decomposer.decompose(requirement)


async def _execute_plan(workspace: str, plan):
    """Execute the development plan."""
    executor = TaskExecutor(
        workspace=workspace,
        max_fix_attempts=3,
        on_progress=_progress_callback,
    )
    return await executor.execute(plan)


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