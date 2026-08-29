"""Provider-agnostic LLM chat with tool calling.

Supports any OpenAI-compatible endpoint (OpenAI, DeepSeek, GLM, OpenRouter,
Ollama, vLLM...) and Anthropic, behind one interface so agents never care
which vendor they talk to.

    from deep_research_agent.llm import chat
    content, tool_calls, usage = chat(spec, messages, tools=defs, role="executor")

Tool definitions are written once in OpenAI schema and converted to
Anthropic format internally. Tool calls come back normalized to
[{"id": str, "name": str, "arguments": dict}].
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any

from .config import ModelSpec
from .usage import TokenTracker

logger = logging.getLogger(__name__)

RETRYABLE_ERRORS = ("rate_limit", "overloaded", "timeout", "connection")
MAX_ATTEMPTS = 4


def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    out = []
    for t in tools:
        fn = t.get("function", t)
        out.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return out


def _normalized_usage(raw: dict[str, Any]) -> tuple[int, int, int]:
    prompt = int(raw.get("prompt_tokens", raw.get("input_tokens", 0)) or 0)
    completion = int(raw.get("completion_tokens", raw.get("output_tokens", 0)) or 0)
    cached = int(raw.get("prompt_tokens_details", {}).get("cached_tokens",
                raw.get("cache_read_input_tokens", 0)) or 0) if isinstance(
        raw.get("prompt_tokens_details"), dict) else int(raw.get("cache_read_input_tokens", 0) or 0)
    return prompt, completion, cached


class LLMError(RuntimeError):
    pass


def chat(spec: ModelSpec,
         messages: list[dict],
         tools: list[dict] | None = None,
         role: str = "agent",
         tracker: TokenTracker | None = None,
         max_tokens: int | None = None) -> tuple[str, list[dict], dict]:
    """Run one chat completion. Returns (content, tool_calls, usage_dict).

    `messages` use the OpenAI layout: {"role": ..., "content": ...}.
    Assistant tool calls may appear as
    {"role": "assistant", "tool_calls": [...]} and tool results as
    {"role": "tool", "tool_call_id": ..., "content": ...}; both are
    translated for Anthropic transparently.
    """
    start = time.time()
    last_err: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            if spec.provider == "anthropic":
                content, tool_calls, usage = _chat_anthropic(
                    spec, messages, tools, max_tokens or spec.max_tokens)
            else:
                content, tool_calls, usage = _chat_openai(
                    spec, messages, tools, max_tokens or spec.max_tokens)
            seconds = time.time() - start
            p, c, k = _normalized_usage(usage)
            if tracker:
                tracker.record(role, p, c, k, spec.model, seconds)
            return content, tool_calls, {"prompt": p, "completion": c,
                                         "cached": k, "seconds": seconds}
        except Exception as e:  # noqa: BLE001 - normalize provider errors
            last_err = e
            msg = str(e).lower()
            if any(k in msg for k in RETRYABLE_ERRORS) and attempt < MAX_ATTEMPTS - 1:
                wait = 2 ** attempt * 2
                logger.warning("LLM call failed (%s), retrying in %ss", e, wait)
                time.sleep(wait)
                continue
            raise LLMError(f"{spec.provider}:{spec.model} failed: {e}") from e
    raise LLMError(f"{spec.provider}:{spec.model} failed after retries: {last_err}")


def _chat_openai(spec: ModelSpec, messages: list[dict],
                 tools: list[dict] | None, max_tokens: int):
    try:
        from openai import OpenAI
    except ImportError as e:
        raise LLMError("openai package not installed; run `pip install openai`") from e
    client = OpenAI(api_key=spec.resolved_api_key(), base_url=spec.base_url)
    kwargs: dict[str, Any] = {"model": spec.model, "messages": messages,
                              "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if spec.reasoning_effort and spec.model.startswith(("o1", "o3", "o4")):
        kwargs["reasoning_effort"] = spec.reasoning_effort
    resp = client.chat.completions.create(**kwargs)
    msg = resp.choices[0].message
    content = msg.content or ""
    tool_calls = []
    for tc in (getattr(msg, "tool_calls", None) or []):
        try:
            args = json.loads(tc.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {"_raw": tc.function.arguments}
        tool_calls.append({"id": tc.id, "name": tc.function.name, "arguments": args})
    usage = {}
    if resp.usage:
        usage = {"prompt_tokens": resp.usage.prompt_tokens or 0,
                 "completion_tokens": resp.usage.completion_tokens or 0,
                 "prompt_tokens_details": getattr(resp.usage, "prompt_tokens_details", None)}
    return content, tool_calls, usage


def _chat_anthropic(spec: ModelSpec, messages: list[dict],
                    tools: list[dict] | None, max_tokens: int):
    try:
        import anthropic
    except ImportError as e:
        raise LLMError("anthropic package not installed; run `pip install anthropic`") from e
    client = anthropic.Anthropic(api_key=spec.resolved_api_key())

    system_texts = [m["content"] for m in messages if m["role"] == "system"]
    convo: list[dict] = []
    for m in messages:
        role, content = m["role"], m.get("content") or ""
        if role == "system":
            continue
        if role == "tool":
            convo.append({"role": "user", "type": "tool_result",
                          "tool_use_id": m.get("tool_call_id", ""), "content": content or ""})
        elif role == "assistant" and m.get("tool_calls"):
            blocks: list[dict] = []
            if content:
                blocks.append({"type": "text", "text": content})
            for tc in m["tool_calls"]:
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"],
                               "input": tc["arguments"]})
            convo.append({"role": "assistant", "content": blocks})
        else:
            convo.append({"role": role, "content": content})

    kwargs: dict[str, Any] = {
        "model": spec.model, "messages": convo, "max_tokens": max_tokens,
        "system": "\n\n".join(system_texts) if system_texts else anthropic.NOT_GIVEN,
    }
    if tools:
        kwargs["tools"] = _openai_tools_to_anthropic(tools)

    resp = client.messages.create(**kwargs)
    text_parts, tool_calls = [], []
    for block in resp.content:
        if block.type == "text":
            text_parts.append(block.text)
        elif block.type == "tool_use":
            tool_calls.append({"id": block.id, "name": block.name,
                               "arguments": dict(block.input or {})})
    usage = {"input_tokens": resp.usage.input_tokens if resp.usage else 0,
             "output_tokens": resp.usage.output_tokens if resp.usage else 0,
             "cache_read_input_tokens": getattr(resp.usage, "cache_read_input_tokens", 0)}
    return "\n".join(text_parts), tool_calls, usage
