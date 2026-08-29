"""Token and cost tracking across planner / executor / wide workers."""
from __future__ import annotations

from dataclasses import dataclass, field

# Rough USD per 1M tokens (prompt, completion). Update as pricing moves.
PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.5, 10.0),
    "gpt-4o-mini": (0.15, 0.6),
    "o1": (15.0, 60.0),
    "o3": (10.0, 40.0),
    "claude-3-7-sonnet-20250219": (3.0, 15.0),
    "claude-sonnet-4-20250514": (3.0, 15.0),
    "deepseek-chat": (0.27, 1.1),
    "glm-4.5": (0.6, 2.2),
}
DEFAULT_PRICE = (1.0, 3.0)


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_prompt_tokens: int = 0
    api_calls: int = 0
    cost: float = 0.0
    seconds: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens

    def add(self, prompt: int, completion: int, cached: int, model: str, seconds: float) -> None:
        p_in, p_out = PRICES.get(model, DEFAULT_PRICE)
        self.prompt_tokens += prompt
        self.completion_tokens += completion
        self.cached_prompt_tokens += cached
        self.api_calls += 1
        self.seconds += seconds
        # Cached prompt tokens are typically billed at ~50%; keep it simple.
        self.cost += (prompt - cached) / 1e6 * p_in + cached / 1e6 * p_in * 0.5 \
            + completion / 1e6 * p_out

    def merge(self, other: "Usage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.cached_prompt_tokens += other.cached_prompt_tokens
        self.api_calls += other.api_calls
        self.cost += other.cost
        self.seconds += other.seconds


@dataclass
class TokenTracker:
    """Aggregates usage per agent role for final reporting."""

    usage_by_role: dict[str, Usage] = field(default_factory=dict)

    def record(self, role: str, prompt: int, completion: int,
               cached: int, model: str, seconds: float) -> None:
        u = self.usage_by_role.setdefault(role, Usage())
        u.add(prompt, completion, cached, model, seconds)

    def report(self) -> str:
        lines = [f"{'role':<12} {'calls':>6} {'prompt':>10} {'completion':>11} {'cost($)':>9} {'time(s)':>8}"]
        total = Usage()
        for role, u in sorted(self.usage_by_role.items()):
            total.merge(u)
            lines.append(f"{role:<12} {u.api_calls:>6} {u.prompt_tokens:>10,} "
                         f"{u.completion_tokens:>11,} {u.cost:>9.4f} {u.seconds:>8.1f}")
        lines.append("-" * 62)
        lines.append(f"{'TOTAL':<12} {total.api_calls:>6} {total.prompt_tokens:>10,} "
                     f"{total.completion_tokens:>11,} {total.cost:>9.4f} {total.seconds:>8.1f}")
        return "\n".join(lines)
