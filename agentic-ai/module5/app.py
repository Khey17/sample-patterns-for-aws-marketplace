# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/app.py
==============
HTTP server for Module 5 Domain-Specific Agent Applications.

Provides REST API endpoints for domain-specialized agent invocations.
Runs on port 8085 by default.
"""

from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from module5.agent import create_domain_agent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = int(os.getenv("MODULE5_PORT", "8085"))
HOST = os.getenv("MODULE5_HOST", "127.0.0.1")
VERBOSE = os.getenv("MODULE5_VERBOSE", "false").lower() == "true"

# ---------------------------------------------------------------------------
# Agent cache — initialized once at startup, reused across requests
# ---------------------------------------------------------------------------

_AGENTS: dict = {}


def _get_agent(domain: str):
    """Return a cached domain agent, creating it on first use."""
    if domain not in _AGENTS:
        _AGENTS[domain] = create_domain_agent(domain, verbose=VERBOSE)
    return _AGENTS[domain]

# ---------------------------------------------------------------------------
# HTTP Request Handler
# ---------------------------------------------------------------------------

class Module5Handler(BaseHTTPRequestHandler):
    """HTTP request handler for Module 5 domain agent endpoints."""

    def _send_json_response(self, data: dict[str, Any], status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def _send_error_response(self, message: str, status: int = 400) -> None:
        self._send_json_response({"error": message}, status)

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path == "/ping":
            self._send_json_response({
                "status": "healthy",
                "service": "module5-domain-agents",
                "version": "0.1.0",
                "domains": ["customer", "geospatial", "voice"],
            })
        else:
            self._send_error_response("Not found", 404)

    def do_POST(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            try:
                data = json.loads(body) if body else {}
            except json.JSONDecodeError:
                self._send_error_response("Invalid JSON in request body")
                return

            if self.path == "/invoke":
                self._handle_invoke(data)
            else:
                self._send_error_response("Not found", 404)

        except Exception as e:
            self._send_error_response(f"Internal server error: {str(e)}", 500)

    def _handle_invoke(self, data: dict[str, Any]) -> None:
        """
        Handle /invoke endpoint.

        Request body:
        {
            "domain": "customer",
            "message": "Find me a monitoring tool"
        }
        """
        domain = data.get("domain")
        message = data.get("message")

        if not domain:
            self._send_error_response("Missing 'domain' in request body")
            return
        if not message:
            self._send_error_response("Missing 'message' in request body")
            return

        try:
            agent = _get_agent(domain)
            result = agent.agent.invoke({"messages": [("user", message)]})
            messages = result.get("messages", [])
            output = messages[-1].content if messages else ""
            self._send_json_response({"status": "success", "domain": domain, "output": output})
        except ValueError as e:
            self._send_error_response(str(e), 400)
        except Exception as e:
            self._send_error_response(f"Agent invocation failed: {str(e)}", 500)

    def log_message(self, format: str, *args: Any) -> None:
        if VERBOSE:
            print(f"[Module5] {format % args}")


# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

def run_server(port: int = PORT, host: str = HOST) -> None:
    server = HTTPServer((host, port), Module5Handler)
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  Module 5: Domain-Specific Agent Applications                   ║
╚══════════════════════════════════════════════════════════════════╝

  Server running on http://{host}:{port}

  Endpoints:
    GET  /ping    - Health check
    POST /invoke  - Invoke a domain agent

  Domains: customer | geospatial | voice

  Example:
    curl -X POST http://localhost:{port}/invoke \\
      -H "Content-Type: application/json" \\
      -d '{{"domain": "customer", "message": "Find me a monitoring tool"}}'

  Press Ctrl+C to stop
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
