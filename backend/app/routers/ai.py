import asyncio
import json
import os
import time
from collections import defaultdict, deque
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from ..security import current_user

router = APIRouter()

# Best-effort application limit for the current single-worker Render deployment.
# Groq also enforces account-level free-plan limits.
_usage: dict[str, deque[float]] = defaultdict(deque)
WINDOW_SECONDS = 3600
MAX_REQUESTS = 10
MAX_CONTEXT_BYTES = 10_000
MAX_QUESTION_CHARS = 500

SYSTEM_PROMPT = """You are PennyPilot AI Coach, a read-only personal-finance explanation assistant.
Use only the supplied aggregated PennyPilot summary. Never invent transactions, merchants, causes, dates, or figures.
Separate recorded facts from general suggestions. Never claim to create, edit, or delete financial data.
Never request passwords, tokens, account/card numbers, UPI PINs, receipts, or credentials.
Do not give personalized investment, tax, legal, lending, or credit instructions.
Mention the supplied comparison period when discussing changes.
Transfers, adjustments, goal allocations, and projected bills are not expenses.
Keep the answer concise, practical, and in Indian English. Say explicitly when the supplied data is insufficient."""

BLOCKED_KEYS = {
    "email", "password", "password_hash", "token", "access_token", "authorization",
    "account_number", "card_number", "upi_pin", "database_url", "receipt", "notes",
    "description", "location", "transaction_id", "user_id"
}

class AIRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    summary: dict[str, Any]


def _validate_summary(value: Any, path: str = "summary") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in BLOCKED_KEYS:
                raise HTTPException(422, f"Sensitive field is not allowed in AI context: {path}.{key}")
            _validate_summary(child, f"{path}.{key}")
    elif isinstance(value, list):
        if len(value) > 20:
            raise HTTPException(422, f"Too many items in {path}")
        for index, child in enumerate(value):
            _validate_summary(child, f"{path}[{index}]")
    elif isinstance(value, str) and len(value) > 500:
        raise HTTPException(422, f"Text field is too long in {path}")


def _rate_limit(user_id: str) -> int:
    now = time.monotonic()
    bucket = _usage[user_id]
    while bucket and now - bucket[0] >= WINDOW_SECONDS:
        bucket.popleft()
    if len(bucket) >= MAX_REQUESTS:
        retry_after = max(1, int(WINDOW_SECONDS - (now - bucket[0])))
        raise HTTPException(429, f"PennyPilot AI free limit reached. Try again in about {retry_after // 60 + 1} minutes.")
    bucket.append(now)
    return MAX_REQUESTS - len(bucket)


@router.post("/ai/coach")
async def ai_coach(data: AIRequest, user=Depends(current_user)):
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
    if not api_key:
        raise HTTPException(503, "PennyPilot AI is not configured yet.")

    _validate_summary(data.summary)
    encoded = json.dumps(data.summary, separators=(",", ":"), ensure_ascii=False)
    if len(encoded.encode("utf-8")) > MAX_CONTEXT_BYTES:
        raise HTTPException(413, "AI summary is too large. Narrow the dashboard period and try again.")

    remaining = _rate_limit(user.id)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Aggregated PennyPilot summary:\n{encoded}\n\nQuestion: {data.question}"},
        ],
        "temperature": 0.2,
        "max_completion_tokens": 800,
        "reasoning_format": "hidden",
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0)) as client:
        response = None
        for attempt in range(2):
            try:
                response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            except httpx.TimeoutException:
                if attempt == 0:
                    await asyncio.sleep(1)
                    continue
                raise HTTPException(504, "PennyPilot AI timed out. Please try again once.")
            if response.status_code in {429, 503} and attempt == 0:
                await asyncio.sleep(1)
                continue
            break

    if response is None:
        raise HTTPException(502, "PennyPilot AI did not return a response.")
    if response.status_code == 429:
        raise HTTPException(429, "The shared Groq free-tier limit is currently reached. Try again later.")
    if response.status_code >= 400:
        # Never expose provider response bodies because they may contain operational details.
        raise HTTPException(502, f"PennyPilot AI provider error ({response.status_code}).")

    try:
        answer = response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, ValueError):
        raise HTTPException(502, "PennyPilot AI returned an invalid response.")
    if not answer:
        raise HTTPException(502, "PennyPilot AI returned an empty response.")

    return {"answer": answer, "remaining_this_hour": remaining, "model": model}