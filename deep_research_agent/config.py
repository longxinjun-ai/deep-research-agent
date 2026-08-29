"""Environment-driven configuration for deep-research-agent.

Everything is configurable through environment variables so the same code
runs against OpenAI, Anthropic, DeepSeek, GLM, OpenRouter, Ollama, or any
OpenAI-compatible endpoint without code changes.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


@dataclass
class ModelSpec:
    """A (provider, model, base_url, api_key) routing tuple."""

    name: str
    provider: str  # "openai_compatible" | "anthropic"
    model: str
    base_url: str | None = None
    api_key: str | None = None
    reasoning_effort: str | None = None  # for o-series style models
    max_tokens: int = 8192

    def resolved_api_key(self) -> str:
        if self.api_key:
            return self.api_key
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY", "")
        if self.base_url and "openrouter" in self.base_url:
            return os.environ.get("OPENROUTER_API_KEY", "")
        if self.base_url and "deepseek" in self.base_url:
            return os.environ.get("DEEPSEEK_API_KEY", "")
        if self.base_url and ("bigmodel" in self.base_url or "glm" in self.base_url):
            return os.environ.get("GLM_API_KEY", "")
        return os.environ.get("OPENAI_API_KEY", "")


@dataclass
class Config:
    """Global config assembled from environment variables."""

    planner: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="planner",
        provider="openai_compatible",
        model=_env("DRA_PLANNER_MODEL", "gpt-4o"),
        base_url=_env("DRA_PLANNER_BASE_URL") or None,
        reasoning_effort=_env("DRA_PLANNER_REASONING_EFFORT") or None,
    ))
    executor: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="executor",
        provider=_env("DRA_EXECUTOR_PROVIDER", "openai_compatible"),
        model=_env("DRA_EXECUTOR_MODEL", "gpt-4o"),
        base_url=_env("DRA_EXECUTOR_BASE_URL") or None,
        reasoning_effort=_env("DRA_EXECUTOR_REASONING_EFFORT") or None,
    ))
    researcher: ModelSpec = field(default_factory=lambda: ModelSpec(
        name="researcher",
        provider=_env("DRA_RESEARCHER_PROVIDER", "openai_compatible"),
        model=_env("DRA_RESEARCHER_MODEL", "gpt-4o-mini"),
        base_url=_env("DRA_RESEARCHER_BASE_URL") or None,
    ))

    # Search backend: "ddgs" (free, default), "tavily" (paid, better)
    search_backend: str = _env("DRA_SEARCH_BACKEND", "ddgs")
    tavily_api_key: str = _env("TAVILY_API_KEY")

    # Safety: require interactive confirmation for shell commands unless set.
    auto_approve: bool = _env("DRA_AUTO_APPROVE", "") in ("1", "true", "yes")
    # Wide-research default worker concurrency.
    wide_workers: int = int(_env("DRA_WIDE_WORKERS", "4"))
    debug: bool = _env("DRA_DEBUG", "") in ("1", "true", "yes")


def load_config() -> Config:
    return Config()
