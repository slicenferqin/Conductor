"""Claude Code CLI Integration."""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, AsyncIterator


@dataclass
class ClaudeMessage:
    """A message from Claude Code CLI."""
    type: str
    content: Any


class ClaudeCodeCLI:
    """Wrapper for Claude Code CLI."""

    def __init__(self, workspace: str) -> None:
        self.workspace = workspace
        self._session_started: set[str] = set()  # Track which sessions have been started

    async def execute(
        self,
        prompt: str,
        session_id: str | None = None,
        allowed_tools: list[str] | None = None,
    ) -> AsyncIterator[ClaudeMessage]:
        """Execute a prompt and stream results."""
        cmd = [
            "claude",
            "--print", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        # For session management:
        # - First call with a session_id: use --session-id to create
        # - Subsequent calls: use --resume to continue
        if session_id:
            if session_id in self._session_started:
                cmd.extend(["--resume", session_id])
            else:
                cmd.extend(["--session-id", session_id])
                self._session_started.add(session_id)

        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])

        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=self.workspace,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if process.stdout is None:
            return

        # Collect stderr for error reporting
        stderr_task = asyncio.create_task(process.stderr.read() if process.stderr else asyncio.sleep(0))

        async for line in process.stdout:
            line_str = line.decode().strip()
            if line_str:
                try:
                    data = json.loads(line_str)
                    yield ClaudeMessage(
                        type=data.get("type", "unknown"),
                        content=data,
                    )
                except json.JSONDecodeError:
                    # Log non-JSON output for debugging
                    print(f"[DEBUG] Non-JSON output: {line_str}", file=sys.stderr)

        await process.wait()

        # Check for errors
        stderr_output = await stderr_task
        if isinstance(stderr_output, bytes) and stderr_output:
            stderr_str = stderr_output.decode().strip()
            if stderr_str and process.returncode != 0:
                print(f"[DEBUG] Claude CLI stderr: {stderr_str}", file=sys.stderr)

    async def execute_and_wait(
        self,
        prompt: str,
        session_id: str | None = None,
        allowed_tools: list[str] | None = None,
    ) -> list[ClaudeMessage]:
        """Execute a prompt and wait for completion."""
        messages = []
        async for msg in self.execute(prompt, session_id, allowed_tools):
            messages.append(msg)
        return messages

    def execute_sync(
        self,
        prompt: str,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Synchronous execution for simple use cases."""
        cmd = [
            "claude",
            "--print", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        if session_id:
            cmd.extend(["--session-id", session_id])

        result = subprocess.run(
            cmd,
            cwd=self.workspace,
            capture_output=True,
            text=True,
        )

        messages = []
        for line in result.stdout.strip().split("\n"):
            if line:
                try:
                    messages.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

        return messages