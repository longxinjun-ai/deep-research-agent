"""File and command tools with a human-confirmation gate.

Everything the executor writes goes through create_file so the run directory
stays auditable. execute_command asks for interactive confirmation unless
DRA_AUTO_APPROVE=1 — user agency is a core principle carried over from
grapeot/deep_research_agent.
"""
from __future__ import annotations

import logging
import shlex
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Commands considered safe to run without confirmation (pure readers).
SAFE_PATTERNS = ("python3 -c 'import", "ls", "cat ", "wc ", "grep ", "sort ", "uniq ")

_blocked = ("rm -rf /", "mkfs", "dd if=", ":(){", "shutdown", "reboot", "halt")


def create_file(filename: str, content: str, session_dir: Path | None = None) -> str:
    """Create/overwrite a file. Paths are confined to the session directory."""
    target = _safe_path(filename, session_dir)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    logger.info("created file: %s (%d chars)", target, len(content))
    return f"Successfully created/updated file: {target.name}"


def read_file(filename: str, session_dir: Path | None = None) -> str:
    target = _safe_path(filename, session_dir)
    if not target.exists():
        return f"[error: file not found: {filename}]"
    return target.read_text(encoding="utf-8")[:50000]


def execute_command(command: str, timeout: int = 120,
                    auto_approve: bool = False, session_dir: Path | None = None) -> str:
    """Run a shell command after user confirmation. Returns combined output."""
    if any(b in command for b in _blocked):
        return "[refused: destructive command blocked]"
    if not auto_approve and not _is_safe(command):
        answer = input(f"\nConfirm execution of command: {command}\nExecute? [y/N]: ")
        if answer.strip().lower() not in ("y", "yes"):
            return "[user declined command execution]"

    cwd = str(session_dir) if session_dir else None
    try:
        proc = subprocess.run(command, shell=True, capture_output=True,
                              text=True, timeout=timeout, cwd=cwd)
        out = (proc.stdout or "") + (("\n[stderr]\n" + proc.stderr) if proc.stderr else "")
        return f"[exit {proc.returncode}]\n{out[:20000]}"
    except subprocess.TimeoutExpired:
        return f"[error: command timed out after {timeout}s]"
    except Exception as e:  # noqa: BLE001
        return f"[error: {e}]"


def _is_safe(command: str) -> bool:
    c = command.strip()
    return any(c.startswith(p.strip()) for p in SAFE_PATTERNS)


def _safe_path(filename: str, session_dir: Path | None) -> Path:
    """Confine paths to the session dir; reject traversal outside it."""
    p = Path(filename)
    if p.is_absolute():
        raise ValueError(f"absolute paths not allowed: {filename}")
    if ".." in p.parts:
        raise ValueError(f"path traversal not allowed: {filename}")
    if session_dir is not None:
        resolved = (session_dir / p).resolve()
        if not str(resolved).startswith(str(session_dir.resolve())):
            raise ValueError(f"path escapes session directory: {filename}")
        return resolved
    return p
