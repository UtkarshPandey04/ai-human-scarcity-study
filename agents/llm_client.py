"""Provider abstraction for the LLM reasoning layer (Phase E). The one rule this file exists to
enforce: **no vendor SDK may leak into agents/llm_reasoning.py.** Every provider difference —
message format, JSON-mode flag, model names — lives here, behind one function:

    complete(messages, schema=None, provider=None, model=None) -> dict

Currently backed by Groq and Gemini (the two providers this project has access to). Adding another
provider later means adding one function here and one entry in PROVIDERS — nothing in
llm_reasoning.py should need to change.

## What "schema" does and doesn't guarantee

`schema` is used two ways: (1) it's always rendered into the prompt as a "respond with exactly this
JSON shape" instruction, for both providers; (2) it is *not* currently passed as a native
structured-output constraint (Gemini's `response_schema` / Groq's `json_schema` response format),
because that would need to be verified against a live account to trust, and this file was built
without one — see INTEGRATION_ISSUES.md-style note in the module: whoever first runs this against a
real key should try wiring `response_schema` through for Gemini specifically (it supports full JSON
Schema natively) and tighten this comment once confirmed working.

Both providers *do* guarantee syntactically valid JSON (`response_format: json_object` for Groq,
`response_mime_type: application/json` for Gemini) — what they don't guarantee is that the JSON
matches our schema's keys/enums. That's exactly why agents/llm_reasoning.py has a retry loop: parse,
validate against our schema, and on failure retry once with the validation error appended before
giving up and logging a parse failure. Don't try to make this file solve that problem — it isn't
supposed to.

## Configuration

Reads API keys from `GROQ_API_KEY` / `GEMINI_API_KEY` environment variables (never hard-code a key,
never accept one as a function argument — that's how a key ends up in a log line or a git diff).
Default provider: `LLM_PROVIDER` env var, else "groq". Default models are set per-provider below;
override with `GROQ_MODEL` / `GEMINI_MODEL` if the defaults are stale by the time this is used for
real — model names go out of date faster than code does.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

from common.env import load_dotenv

load_dotenv()  # pulls GROQ_API_KEY / GEMINI_API_KEY etc. from a local .env, if one exists


class LLMCompletionError(RuntimeError):
    """Raised when a provider call fails outright or returns text that isn't valid JSON at all.
    Distinct from "valid JSON but wrong shape for our schema" — that's agents/llm_reasoning.py's
    retry loop's job, not this file's.
    """


class LLMRateLimitError(LLMCompletionError):
    """A specific, more useful subtype of LLMCompletionError: the provider refused the request
    for quota/rate-limit reasons (HTTP 429), not because anything was wrong with the request.

    This distinction matters for what ends up in the paper. Caught live: a Gemini free-tier quota
    of 20 requests/day for a specific model produced a batch of failures that looked, from
    meta.llm_parse_failure alone, exactly like the model producing bad output 69% of the time —
    which would have been a false and damaging claim about the model if it had gone in a results
    table unexamined. agents/llm_reasoning.py tags these separately (meta.llm_rate_limited) so the
    parse-failure-rate metric stays a measure of model output quality, not of this project's quota
    headroom.
    """


@dataclass(frozen=True)
class ChatMessage:
    """role: "system" | "user" | "assistant". Named ChatMessage, not Message, to avoid colliding
    with common.actions.Message (a game-level structured claim — a completely different thing)."""

    role: str
    content: str


DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "groq")
# Verified against this project's live keys on 2026-09-10 — both `llama-3.3-70b-versatile`
# (Groq) and `gemini-2.5-flash` (Gemini) had been deprecated/retired since this file's original
# knowledge cutoff. Re-verify with `client.models.list()` (Groq) if this ever 404s again — model
# names go stale faster than code does; see the module docstring.
DEFAULT_GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-20b")
GROQ_MAX_RETRIES = int(os.environ.get("GROQ_MAX_RETRIES", "6"))
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
DEFAULT_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
DEFAULT_OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "liquid/lfm-2.5-2.6b:free")

_groq_key_idx = 0
_gemini_key_idx = 0


def get_groq_api_keys() -> list[str]:
    raw = os.environ.get("GROQ_API_KEYS") or os.environ.get("GROQ_API_KEY") or ""
    return [k.strip() for k in raw.split(",") if k.strip()]


def get_gemini_api_keys() -> list[str]:
    raw = os.environ.get("GEMINI_API_KEYS") or os.environ.get("GEMINI_API_KEY") or ""
    return [k.strip() for k in raw.split(",") if k.strip()]


def _schema_instruction(schema: dict | None) -> str | None:
    if schema is None:
        return None
    return (
        "Respond with a single JSON object matching exactly this shape (no prose, no markdown "
        f"fences, just the JSON object):\n{json.dumps(schema, indent=2)}"
    )


def _messages_with_schema(messages: list[ChatMessage], schema: dict | None) -> list[ChatMessage]:
    instruction = _schema_instruction(schema)
    if instruction is None:
        return messages
    last = messages[-1]
    return [*messages[:-1], ChatMessage(role=last.role, content=f"{last.content}\n\n{instruction}")]


def _parse_json(text: str, provider: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise LLMCompletionError(f"{provider} did not return valid JSON: {exc}\n---\n{text}") from exc


def _complete_groq(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    from groq import Groq, RateLimitError

    keys = get_groq_api_keys()
    if not keys:
        raise LLMCompletionError("GROQ_API_KEY is not set")

    global _groq_key_idx
    payload = _messages_with_schema(messages, schema)
    create_kwargs = {
        "model": model or DEFAULT_GROQ_MODEL,
        "messages": [{"role": m.role, "content": m.content} for m in payload],
        "temperature": temperature,
    }
    if schema is not None:
        create_kwargs["response_format"] = {"type": "json_object"}

    last_rate_limit = None
    for attempt in range(len(keys)):
        curr_key = keys[(_groq_key_idx + attempt) % len(keys)]
        client = Groq(api_key=curr_key, max_retries=GROQ_MAX_RETRIES)
        try:
            response = client.chat.completions.create(**create_kwargs)
            _groq_key_idx = (_groq_key_idx + attempt + 1) % len(keys)
            if usage is not None and response.usage is not None:
                usage["prompt_tokens"] = response.usage.prompt_tokens
                usage["completion_tokens"] = response.usage.completion_tokens
                usage["model"] = model or DEFAULT_GROQ_MODEL
                usage["provider"] = "groq"
            text = response.choices[0].message.content
            return _parse_json(text, "groq")
        except RateLimitError as exc:
            last_rate_limit = exc
            continue
        except Exception as exc:
            raise LLMCompletionError(f"groq request failed: {exc}") from exc

    if last_rate_limit:
        raise LLMRateLimitError(f"groq rate limit across all {len(keys)} key(s): {last_rate_limit}") from last_rate_limit
    raise LLMCompletionError("groq request failed on all configured keys")


def _complete_gemini(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    from google import genai
    from google.genai import errors, types

    keys = get_gemini_api_keys()
    if not keys:
        raise LLMCompletionError("GEMINI_API_KEY is not set")

    global _gemini_key_idx
    payload = _messages_with_schema(messages, schema)
    system_parts = [m.content for m in payload if m.role == "system"]
    contents = [
        types.Content(role=("model" if m.role == "assistant" else "user"), parts=[types.Part(text=m.content)])
        for m in payload
        if m.role != "system"
    ]
    config = types.GenerateContentConfig(
        temperature=temperature,
        response_mime_type="application/json" if schema is not None else None,
        system_instruction="\n\n".join(system_parts) or None,
    )

    last_rate_limit = None
    for attempt in range(len(keys)):
        curr_key = keys[(_gemini_key_idx + attempt) % len(keys)]
        client = genai.Client(api_key=curr_key)
        try:
            response = client.models.generate_content(
                model=model or DEFAULT_GEMINI_MODEL, contents=contents, config=config
            )
            _gemini_key_idx = (_gemini_key_idx + attempt + 1) % len(keys)
            if usage is not None and response.usage_metadata is not None:
                usage["prompt_tokens"] = response.usage_metadata.prompt_token_count
                usage["completion_tokens"] = response.usage_metadata.candidates_token_count
                usage["model"] = model or DEFAULT_GEMINI_MODEL
                usage["provider"] = "gemini"
            return _parse_json(response.text, "gemini")
        except errors.APIError as exc:
            if exc.code == 429:
                last_rate_limit = exc
                continue
            raise LLMCompletionError(f"gemini request failed: {exc}") from exc
        except Exception as exc:
            raise LLMCompletionError(f"gemini request failed: {exc}") from exc

    if last_rate_limit:
        raise LLMRateLimitError(f"gemini rate limit across all {len(keys)} key(s): {last_rate_limit}") from last_rate_limit
    raise LLMCompletionError("gemini request failed on all configured keys")


def _complete_openai_compatible(
    messages: list[ChatMessage],
    schema: dict | None,
    model: str | None,
    temperature: float,
    usage: dict | None,
    *,
    api_key: str,
    base_url: str,
    default_model: str,
    provider_name: str,
) -> dict:
    import httpx

    payload = _messages_with_schema(messages, schema)
    req_body = {
        "model": model or default_model,
        "messages": [{"role": m.role, "content": m.content} for m in payload],
        "temperature": temperature,
    }
    if schema is not None:
        req_body["response_format"] = {"type": "json_object"}
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    timeout_sec = 6.0 if provider_name == "ollama" else 30.0
    try:
        resp = httpx.post(f"{base_url.rstrip('/')}/chat/completions", json=req_body, headers=headers, timeout=timeout_sec)
        if resp.status_code == 429:
            raise LLMRateLimitError(f"{provider_name} rate limit: {resp.text}")
        if resp.status_code != 200:
            raise LLMCompletionError(f"{provider_name} request failed ({resp.status_code}): {resp.text}")
        data = resp.json()
        if usage is not None and "usage" in data:
            usage["prompt_tokens"] = data["usage"].get("prompt_tokens", 0)
            usage["completion_tokens"] = data["usage"].get("completion_tokens", 0)
            usage["model"] = model or default_model
            usage["provider"] = provider_name
        text = data["choices"][0]["message"]["content"]
        return _parse_json(text, provider_name)
    except (LLMRateLimitError, LLMCompletionError):
        raise
    except httpx.ConnectError as exc:
        raise LLMCompletionError(f"{provider_name} service unreachable at {base_url}: {exc}") from exc
    except httpx.TimeoutException as exc:
        raise LLMCompletionError(f"{provider_name} request timed out: {exc}") from exc
    except Exception as exc:
        raise LLMCompletionError(f"{provider_name} call failed: {exc}") from exc


def is_ollama_available() -> bool:
    """Check if the local or configured Ollama instance is reachable."""
    import httpx
    base_url = (os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    # Check parent root if ends with /v1
    ping_url = base_url[:-3] if base_url.endswith("/v1") else base_url
    try:
        r = httpx.get(f"{ping_url}/api/tags", timeout=1.5)
        return r.status_code == 200
    except Exception:
        return False


def _complete_ollama(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    base_url = os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL
    return _complete_openai_compatible(
        messages,
        schema,
        model,
        temperature,
        usage,
        api_key=os.environ.get("OLLAMA_API_KEY", "ollama"),
        base_url=base_url,
        default_model=DEFAULT_OLLAMA_MODEL,
        provider_name="ollama",
    )


def _complete_openrouter(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise LLMCompletionError("OPENROUTER_API_KEY is not set")
    return _complete_openai_compatible(
        messages,
        schema,
        model,
        temperature,
        usage,
        api_key=key,
        base_url="https://openrouter.ai/api/v1",
        default_model=DEFAULT_OPENROUTER_MODEL,
        provider_name="openrouter",
    )


PROVIDERS = {
    "groq": _complete_groq,
    "gemini": _complete_gemini,
    "ollama": _complete_ollama,
    "openrouter": _complete_openrouter,
}

# Optional throttle hook for a trial campaign (agents/run_ai_trials.py, Phase G) making many calls
# across a worker pool. `complete()` calls this (if set) before every provider request — deliberately
# a single callable, not a class, so this file stays the one place that knows nothing about how the
# limiter is implemented (token bucket, fixed delay, whatever the caller chooses).
_rate_limiter = None  # Callable[[], None] | None


def set_rate_limiter(fn) -> None:
    """`fn` is called with no arguments immediately before every provider request; it should block
    until the caller is allowed to proceed. Pass None to clear it (the default: unthrottled)."""
    global _rate_limiter
    _rate_limiter = fn


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TELEMETRY_PATH = os.path.join(PROJECT_ROOT, "data", "api_telemetry.json")


def _default_provider_stat() -> dict:
    return {
        "total_calls": 0,
        "successful_calls": 0,
        "rate_limited_calls": 0,
        "failed_calls": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_latency_ms": 0.0,
        "avg_latency_ms": 0.0,
        "last_latency_ms": 0.0,
        "last_status": "Idle",
        "last_call_at": None,
    }


def _load_telemetry() -> dict:
    all_providers = ["groq", "gemini", "openrouter", "ollama"]
    base = {p: _default_provider_stat() for p in all_providers}
    if os.path.exists(TELEMETRY_PATH):
        try:
            with open(TELEMETRY_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                if isinstance(loaded, dict):
                    for k, v in loaded.items():
                        if k in base and isinstance(v, dict):
                            base[k].update(v)
                        elif isinstance(v, dict) and k in all_providers:
                            base[k] = v
                    return base
        except Exception:
            pass
    return base


def _save_telemetry(data: dict) -> None:
    try:
        os.makedirs(os.path.dirname(TELEMETRY_PATH), exist_ok=True)
        with open(TELEMETRY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def record_api_call(
    provider: str,
    success: bool,
    latency_ms: float,
    is_rate_limit: bool = False,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    data = _load_telemetry()
    if provider not in data:
        data[provider] = {
            "total_calls": 0,
            "successful_calls": 0,
            "rate_limited_calls": 0,
            "failed_calls": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_latency_ms": 0.0,
            "avg_latency_ms": 0.0,
            "last_latency_ms": 0.0,
            "last_status": "Idle",
            "last_call_at": None,
        }
    stat = data[provider]
    stat["total_calls"] += 1
    if success:
        stat["successful_calls"] += 1
        stat["last_status"] = "Healthy"
    elif is_rate_limit:
        stat["rate_limited_calls"] += 1
        stat["last_status"] = "Rate Limited (429)"
    else:
        stat["failed_calls"] += 1
        stat["last_status"] = "Error"
    stat["total_prompt_tokens"] += prompt_tokens
    stat["total_completion_tokens"] += completion_tokens
    stat["total_latency_ms"] += latency_ms
    stat["last_latency_ms"] = round(latency_ms, 1)
    stat["avg_latency_ms"] = round(stat["total_latency_ms"] / max(1, stat["total_calls"]), 1)
    stat["last_call_at"] = datetime.now(timezone.utc).isoformat()
    _save_telemetry(data)


def get_api_telemetry() -> dict:
    """Retrieve aggregate telemetry dictionary across all providers."""
    return _load_telemetry()


def ping_provider(provider: str) -> dict:
    """Run a live round-trip test against a specific provider to measure latency and status."""
    start = time.time()
    try:
        test_msg = [ChatMessage(role="user", content="Respond with valid JSON: {\"ping\": \"pong\"}")]
        res = complete(test_msg, provider=provider)
        duration_ms = round((time.time() - start) * 1000, 1)
        return {
            "status": "ok",
            "latency_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "response": res,
        }
    except LLMRateLimitError as exc:
        duration_ms = round((time.time() - start) * 1000, 1)
        return {
            "status": "rate_limited",
            "latency_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }
    except Exception as exc:
        duration_ms = round((time.time() - start) * 1000, 1)
        return {
            "status": "error",
            "latency_ms": duration_ms,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(exc),
        }


# In-memory prompt cache to save rate limits on repetitive rounds
_COMPLETION_CACHE: dict[str, dict] = {}
MAX_CACHE_ENTRIES = 500


def clear_completion_cache() -> None:
    """Clear in-memory completion cache."""
    _COMPLETION_CACHE.clear()


FALLBACK_CHAINS = {
    "groq": ["gemini", "openrouter", "ollama"],
    "gemini": ["groq", "openrouter", "ollama"],
    "openrouter": ["groq", "gemini", "ollama"],
    "ollama": ["groq", "gemini", "openrouter"],
}


def complete(
    messages: list[ChatMessage],
    schema: dict | None = None,
    *,
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.4,
    usage: dict | None = None,
) -> dict:
    """The one entry point agents/llm_reasoning.py should ever call.
    Includes in-memory cache and resilient multi-tier fallback (Groq -> Gemini -> OpenRouter -> Ollama).
    """
    target_provider = provider or DEFAULT_PROVIDER
    if target_provider not in PROVIDERS:
        raise ValueError(f"unknown provider {target_provider!r}, must be one of {sorted(PROVIDERS)}")

    # Check in-memory cache if caching is active
    cache_enabled = os.environ.get("LLM_CACHE_ENABLED", "1").lower() in ("1", "true", "yes")
    cache_key = None
    if cache_enabled:
        import copy
        msg_str = "|".join(f"{m.role}:{m.content}" for m in messages)
        cache_key = f"{target_provider}:{model or 'default'}:{msg_str}"
        if cache_key in _COMPLETION_CACHE:
            cached_data = _COMPLETION_CACHE[cache_key]
            if usage is not None:
                usage["cached"] = True
                usage["provider"] = target_provider
                usage["model"] = model or "cached"
            return copy.deepcopy(cached_data)

    if _rate_limiter is not None:
        _rate_limiter()

    start_time = time.time()
    call_usage = usage if usage is not None else {}
    try:
        res = PROVIDERS[target_provider](messages, schema, model, temperature, call_usage)
        duration_ms = (time.time() - start_time) * 1000.0
        record_api_call(
            target_provider,
            success=True,
            latency_ms=duration_ms,
            prompt_tokens=call_usage.get("prompt_tokens", 0),
            completion_tokens=call_usage.get("completion_tokens", 0),
        )
        if cache_enabled and cache_key:
            import copy
            if len(_COMPLETION_CACHE) >= MAX_CACHE_ENTRIES:
                _COMPLETION_CACHE.pop(next(iter(_COMPLETION_CACHE)))
            _COMPLETION_CACHE[cache_key] = copy.deepcopy(res)
        return res
    except Exception as exc:
        duration_ms = (time.time() - start_time) * 1000.0
        is_rl = isinstance(exc, LLMRateLimitError)
        record_api_call(target_provider, success=False, latency_ms=duration_ms, is_rate_limit=is_rl)
        
        # Multi-tier fallback chain: try alternative providers down to zero-cost Ollama fallback
        candidates = FALLBACK_CHAINS.get(target_provider, ["groq", "gemini", "openrouter", "ollama"])
        for fallback in candidates:
            if fallback in PROVIDERS and fallback != target_provider:
                if fallback == "gemini" and not get_gemini_api_keys():
                    continue
                if fallback == "groq" and not get_groq_api_keys():
                    continue
                if fallback == "openrouter" and not os.environ.get("OPENROUTER_API_KEY"):
                    continue
                if fallback == "ollama" and not is_ollama_available():
                    continue
                fb_start = time.time()
                try:
                    res = PROVIDERS[fallback](messages, schema, None, temperature, call_usage)
                    fb_duration = (time.time() - fb_start) * 1000.0
                    call_usage["fallback_from"] = target_provider
                    record_api_call(
                        fallback,
                        success=True,
                        latency_ms=fb_duration,
                        prompt_tokens=call_usage.get("prompt_tokens", 0),
                        completion_tokens=call_usage.get("completion_tokens", 0),
                    )
                    return res
                except Exception:
                    continue
        raise
