"""
module6/activities/_endpoints.py
=================================
HTTP client for calling Module 1/2/3 endpoints from Temporal activities.

Each activity prefers calling the owning module's HTTP endpoint (which
handles Bedrock internally). If the endpoint is unreachable, the activity
falls back to mock responses — no direct Bedrock dependency in module 6.
"""

from __future__ import annotations

import json
import os
import random
import time
import urllib.request
import urllib.error
from typing import Any


MODULE_ENDPOINTS = {
    "module1": os.getenv("MODULE1_URL", "http://localhost:8080"),
    "module2": os.getenv("MODULE2_URL", "http://localhost:8081"),
    "module3": os.getenv("MODULE3_URL", "http://localhost:8082"),
}

_PING_TIMEOUT = 2
_CALL_TIMEOUT = 60

_endpoint_status: dict[str, bool | None] = {}


def is_endpoint_live(module: str) -> bool:
    """Check if a module endpoint is reachable (cached per process)."""
    if module in _endpoint_status:
        return _endpoint_status[module]

    base_url = MODULE_ENDPOINTS.get(module, "")
    if not base_url:
        _endpoint_status[module] = False
        return False

    try:
        req = urllib.request.Request(f"{base_url}/ping", method="GET")
        with urllib.request.urlopen(req, timeout=_PING_TIMEOUT) as resp:
            _endpoint_status[module] = resp.status == 200
    except (urllib.error.URLError, OSError, TimeoutError):
        _endpoint_status[module] = False

    return _endpoint_status[module]


def call_endpoint(module: str, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
    """POST JSON to a module endpoint. Returns parsed response or None on failure."""
    base_url = MODULE_ENDPOINTS.get(module, "")
    url = f"{base_url}{path}"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=_CALL_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
        return None


def reset_endpoint_cache() -> None:
    """Clear cached endpoint status (useful for testing)."""
    _endpoint_status.clear()


# ---------------------------------------------------------------------------
# Simulated delay for mock responses
# ---------------------------------------------------------------------------

def sim_work_delay() -> None:
    """Sleep 0.5-1.5s to simulate work. Skipped when AGENT_NO_DELAY=true."""
    if os.getenv("AGENT_NO_DELAY", "").lower() == "true":
        return
    time.sleep(random.uniform(0.5, 1.5))
