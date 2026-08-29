"""Web search and content extraction.

Backends (auto-detected, graceful degradation):
- search: Tavily (if DRA_SEARCH_BACKEND=tavily and key present) -> ddgs (free)
- fetch:  httpx + trafilatura (readability extraction); falls back to raw
  HTML stripping; optional Playwright when installed for JS-heavy pages.

All results are cached under the session's raw/ directory so retries never
re-fetch the same URL (cache-first principle from the wide-research playbook).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import httpx
    _HTTPX = True
except ImportError:  # pragma: no cover
    _HTTPX = False


def _cache_key(text: str) -> str:
    return hashlib.sha1(text.encode()).hexdigest()[:16]


# --------------------------------------------------------------------- search
def web_search(query: str, max_results: int = 8,
               cache_dir: Path | None = None) -> list[dict]:
    """Return [{"title", "url", "snippet"}]. Never raises; failures return []."""
    key = _cache_key("search:" + query)
    if cache_dir is not None:
        cached = Path(cache_dir) / f"{key}.json"
        if cached.exists():
            return json.loads(cached.read_text(encoding="utf-8"))

    results: list[dict] = []
    import os
    if os.environ.get("DRA_SEARCH_BACKEND") == "tavily" and os.environ.get("TAVILY_API_KEY"):
        results = _search_tavily(query, max_results)
    if not results:
        results = _search_ddgs(query, max_results)

    if cache_dir is not None and results:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        (Path(cache_dir) / f"{key}.json").write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results


def _search_tavily(query: str, max_results: int) -> list[dict]:
    try:
        resp = httpx.post(
            "https://api.tavily.com/search",
            json={"api_key": "", "query": query, "max_results": max_results,
                  "search_depth": "advanced"},
            timeout=30,
        )
        # Tavily now prefers header auth; try both.
        if resp.status_code != 200:
            import os
            resp = httpx.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {os.environ['TAVILY_API_KEY']}"},
                json={"query": query, "max_results": max_results,
                      "search_depth": "advanced"},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        return [{"title": r.get("title", ""), "url": r.get("url", ""),
                 "snippet": r.get("content", "")} for r in data.get("results", [])]
    except Exception as e:  # noqa: BLE001
        logger.warning("Tavily search failed: %s", e)
        return []


def _search_ddgs(query: str, max_results: int) -> list[dict]:
    try:  # package was renamed duckduckgo_search -> ddgs in 2025
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            return [{"title": r.get("title", ""), "url": r.get("href", r.get("url", "")),
                     "snippet": r.get("body", "")}
                    for r in ddgs.text(query, max_results=max_results)]
    except Exception as e:  # noqa: BLE001
        logger.warning("ddgs search failed: %s", e)
        return []


# ---------------------------------------------------------------------- fetch
def fetch_web_content(url: str, max_chars: int = 20000,
                      cache_dir: Path | None = None) -> str:
    """Fetch a URL and return readable text. Cached; never raises."""
    key = _cache_key("fetch:" + url)
    if cache_dir is not None:
        cached = Path(cache_dir) / f"{key}.txt"
        if cached.exists():
            return cached.read_text(encoding="utf-8")[:max_chars]

    text = ""
    try:
        r = httpx.get(url, timeout=30, follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (deep-research-agent)"})
        r.raise_for_status()
        html = r.text
    except Exception as e:  # noqa: BLE001
        html, text = "", f"[fetch error: {e}]"

    if html:
        text = _extract_readable(html, url)

    if cache_dir is not None and text:
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        (Path(cache_dir) / f"{key}.txt").write_text(text, encoding="utf-8")
    return text[:max_chars]


def _extract_readable(html: str, url: str) -> str:
    try:
        import trafilatura
        extracted = trafilatura.extract(html, include_comments=False,
                                        include_tables=True)
        if extracted and len(extracted) > 200:
            return extracted
    except ImportError:
        pass
    except Exception as e:  # noqa: BLE001
        logger.debug("trafilatura failed on %s: %s", url, e)
    # crude fallback: strip tags
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
