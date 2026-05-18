"""
orchestration/activities/_http_client.py
=========================================
Async HTTP client for calling Module 2/3 endpoints from activities.
"""

from __future__ import annotations

import os
from typing import Any

import httpx

_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=60.0)
    return _client


async def call_module2(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST to Module 2 endpoint. Returns parsed JSON or None on failure."""
    base_url = os.getenv("MODULE2_URL", "http://localhost:8081")
    client = _get_client()
    try:
        resp = await client.post(f"{base_url}{path}", json=payload)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, Exception):
        return None


async def call_module3(path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST to Module 3 endpoint. Returns parsed JSON or None on failure."""
    base_url = os.getenv("MODULE3_URL", "http://localhost:8082")
    client = _get_client()
    try:
        resp = await client.post(f"{base_url}{path}", json=payload)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, Exception):
        return None


async def is_module_live(module: str) -> bool:
    """Check if a module endpoint is reachable."""
    urls = {
        "module2": os.getenv("MODULE2_URL", "http://localhost:8081"),
        "module3": os.getenv("MODULE3_URL", "http://localhost:8082"),
    }
    base_url = urls.get(module)
    if not base_url:
        return False
    client = _get_client()
    try:
        resp = await client.get(f"{base_url}/ping", timeout=2.0)
        return resp.status_code == 200
    except (httpx.HTTPError, Exception):
        return False
