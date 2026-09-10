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
from dataclasses import dataclass

from common.env import load_dotenv

load_dotenv()  # pulls GROQ_API_KEY / GEMINI_API_KEY etc. from a local .env, if one exists


class LLMCompletionError(RuntimeError):
    """Raised when a provider call fails outright or returns text that isn't valid JSON at all.
    Distinct from "valid JSON but wrong shape for our schema" — that's agents/llm_reasoning.py's
    retry loop to handle, not this file's.
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
DEFAULT_GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")


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
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMCompletionError(f"{provider} did not return valid JSON: {exc}\n---\n{text}") from exc


def _complete_groq(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    from groq import Groq

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise LLMCompletionError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)
    payload = _messages_with_schema(messages, schema)
    create_kwargs = {
        "model": model or DEFAULT_GROQ_MODEL,
        "messages": [{"role": m.role, "content": m.content} for m in payload],
        "temperature": temperature,
    }
    if schema is not None:
        # Groq requires the word "json" somewhere in the messages to use this mode — guaranteed
        # here since `schema` being non-None means `_messages_with_schema` appended an instruction
        # that says "JSON object". Only request it when a schema was actually asked for: forcing
        # JSON mode unconditionally would break plain-text completions, and did — caught live,
        # `complete()` with no schema 400'd with "'messages' must contain the word 'json'".
        create_kwargs["response_format"] = {"type": "json_object"}
    try:
        response = client.chat.completions.create(**create_kwargs)
    except Exception as exc:  # groq.APIError and friends — normalize to one exception type
        raise LLMCompletionError(f"groq request failed: {exc}") from exc

    if usage is not None and response.usage is not None:
        usage["prompt_tokens"] = response.usage.prompt_tokens
        usage["completion_tokens"] = response.usage.completion_tokens
        usage["model"] = model or DEFAULT_GROQ_MODEL
        usage["provider"] = "groq"

    text = response.choices[0].message.content
    return _parse_json(text, "groq")


def _complete_gemini(
    messages: list[ChatMessage], schema: dict | None, model: str | None, temperature: float, usage: dict | None
) -> dict:
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMCompletionError("GEMINI_API_KEY is not set")

    client = genai.Client(api_key=api_key)
    payload = _messages_with_schema(messages, schema)

    # Gemini has no "system" role in `contents`; system messages become system_instruction, and
    # "assistant" becomes "model" (contents accepts only "user"/"model").
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
    try:
        response = client.models.generate_content(
            model=model or DEFAULT_GEMINI_MODEL, contents=contents, config=config
        )
    except Exception as exc:  # google.genai errors — normalize to one exception type
        raise LLMCompletionError(f"gemini request failed: {exc}") from exc

    if usage is not None and response.usage_metadata is not None:
        usage["prompt_tokens"] = response.usage_metadata.prompt_token_count
        usage["completion_tokens"] = response.usage_metadata.candidates_token_count
        usage["model"] = model or DEFAULT_GEMINI_MODEL
        usage["provider"] = "gemini"

    return _parse_json(response.text, "gemini")


PROVIDERS = {
    "groq": _complete_groq,
    "gemini": _complete_gemini,
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

    Raises LLMCompletionError on any failure: missing API key, network/API error, or text that
    isn't valid JSON at all. Does NOT validate the returned dict against `schema` beyond that — see
    the module docstring for why, and agents/llm_reasoning.py for the retry loop that does.

    Pass a mutable `usage` dict to have it filled in-place with `prompt_tokens`,
    `completion_tokens`, `model`, and `provider` — for agents/PHASE_PLAN.md Phase E's "log tokens
    and cost per trial into meta" requirement, without complicating the return type for callers
    that don't care.
    """
    provider = provider or DEFAULT_PROVIDER
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}, must be one of {sorted(PROVIDERS)}")
    return PROVIDERS[provider](messages, schema, model, temperature, usage)
