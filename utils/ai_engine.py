from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Optional

import httpx

from . import config


@dataclass
class ChatResult:
    ok: bool
    text: str
    error: Optional[str] = None


@dataclass
class EmbedResult:
    ok: bool
    vector: list[float] = field(default_factory=list)
    error: Optional[str] = None


async def _chat_async(
    prompt: str,
    system_prompt: str = config.DEFAULT_SYSTEM_PROMPT,
    temperature: float = config.CHAT_TEMPERATURE,
    max_tokens: int = config.CHAT_MAX_TOKENS,
    client: Optional[httpx.AsyncClient] = None,
) -> ChatResult:
    payload = {
        "model": "qwen",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT)

    try:
        resp = await client.post(config.LLAMA_CHAT_ENDPOINT, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return ChatResult(ok=True, text=content)
    except httpx.ConnectError:
        return ChatResult(
            ok=False,
            text="",
            error=(
                f"Cannot reach llama-server at {config.LLAMA_HOST}. "
                "Is it running?"
            ),
        )
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:300]
        except Exception:
            pass
        return ChatResult(ok=False, text="", error=f"Model error (400): {detail or e}")
    except (KeyError, IndexError, ValueError) as e:
        return ChatResult(ok=False, text="", error=f"Model error: {e}")
    except Exception as e:
        return ChatResult(ok=False, text="", error=str(e))
    finally:
        if owns_client:
            await client.aclose()


async def _embed_async(
    text: str,
    client: Optional[httpx.AsyncClient] = None,
) -> EmbedResult:
    payload = {"input": [text]}

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=config.EMBED_TIMEOUT)

    try:
        resp = await client.post(config.LLAMA_EMBED_ENDPOINT, json=payload)
        resp.raise_for_status()
        data = resp.json()
        vector = data["data"][0]["embedding"]
        return EmbedResult(ok=True, vector=vector)
    except httpx.ConnectError:
        return EmbedResult(ok=False, error="Embedding server unreachable.")
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:300]
        except Exception:
            pass
        return EmbedResult(ok=False, error=f"Embedding error (400): {detail or e}")
    except (KeyError, IndexError, ValueError) as e:
        return EmbedResult(ok=False, error=f"Embedding error: {e}")
    except Exception as e:
        return EmbedResult(ok=False, error=str(e))
    finally:
        if owns_client:
            await client.aclose()


async def _call_many_async(jobs: list[dict]) -> list[ChatResult]:
    async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
        tasks = [
            _chat_async(
                prompt=j["prompt"],
                system_prompt=j.get("system_prompt", config.DEFAULT_SYSTEM_PROMPT),
                client=client,
            )
            for j in jobs
        ]
        return await asyncio.gather(*tasks)


def _run(coro):
    try:
        return asyncio.run(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()


def query_model(
    prompt: str,
    system_prompt: str = config.DEFAULT_SYSTEM_PROMPT,
    temperature: float = config.CHAT_TEMPERATURE,
    max_tokens: int = config.CHAT_MAX_TOKENS,
) -> ChatResult:
    return _run(_chat_async(prompt, system_prompt, temperature, max_tokens))


def embed_text(text: str) -> EmbedResult:
    return _run(_embed_async(text))


def query_model_many(jobs: list[dict]) -> list[ChatResult]:
    return _run(_call_many_async(jobs))
