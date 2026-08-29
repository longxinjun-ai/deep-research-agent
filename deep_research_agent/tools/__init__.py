"""Tool registry: OpenAI-schema definitions + dispatch to implementations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from . import files, web

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": ("Search the web. Returns a list of results with title, "
                            "url and snippet. Use varied keywords across multiple "
                            "calls; aim for >=10 distinct sources per topic."),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search keywords"},
                    "max_results": {"type": "integer", "description": "Max results (default 8)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_content",
            "description": ("Fetch a URL and return readable text (cached). "
                            "Always fetch pages directly relevant to your task; "
                            "never fabricate their content."),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "max_chars": {"type": "integer", "description": "Max characters to return"},
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create or overwrite a file inside the session directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filename", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the session directory.",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": ("Run a shell command (data analysis, scripts) after user "
                            "confirmation. Working directory is the session directory."),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string"},
                    "timeout": {"type": "integer", "description": "Timeout seconds (default 120)"},
                },
                "required": ["command"],
            },
        },
    },
]


def build_dispatcher(session_dir: Path | None = None,
                     auto_approve: bool = False) -> Callable[[str, dict], str]:
    """Return a name -> result-string dispatcher bound to one session."""

    def dispatch(name: str, args: dict) -> str:
        if name == "web_search":
            return json.dumps(
                web.web_search(args["query"], int(args.get("max_results", 8)),
                               cache_dir=Path(session_dir) / "raw" if session_dir else None),
                ensure_ascii=False)
        if name == "fetch_web_content":
            return web.fetch_web_content(
                args["url"], int(args.get("max_chars", 20000)),
                cache_dir=Path(session_dir) / "raw" if session_dir else None)
        if name == "create_file":
            return files.create_file(args["filename"], args["content"], session_dir)
        if name == "read_file":
            return files.read_file(args["filename"], session_dir)
        if name == "execute_command":
            return files.execute_command(args["command"],
                                         int(args.get("timeout", 120)),
                                         auto_approve, session_dir)
        return f"[error: unknown tool {name}]"

    return dispatch
