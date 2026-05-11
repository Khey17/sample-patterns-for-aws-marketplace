# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/algolia_tools.py
================================
Algolia AI semantic search tool for the customer engagement domain.

Uses the Algolia Search SDK in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when the SDK / credentials are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_algolia_semantic_search

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def algolia_semantic_search(query: str, index_name: str = "devops-companion-catalog") -> str:
    """Search product catalog using Algolia AI semantic search.

    Performs a semantic search against the specified Algolia index and returns
    ranked product hits with scores, descriptions, and pricing.

    Args:
        query: Natural language search query (e.g. "monitoring dashboard for ECS").
        index_name: Algolia index to search (default: devops-companion-catalog).

    Returns:
        JSON string with Output_Envelope containing ranked product hits.
    """
    if _is_mock():
        return json.dumps(mock_algolia_semantic_search(query=query, index_name=index_name), indent=2)
    try:
        from algoliasearch.search.client import SearchClientSync

        client = SearchClientSync(
            os.environ["ALGOLIA_APP_ID"], os.environ["ALGOLIA_API_KEY"]
        )
        response = client.search_single_index(index_name, {"query": query, "hitsPerPage": 5})
        return json.dumps(
            {
                "tool": "algolia_semantic_search",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "hits": [h.to_dict() for h in response.hits],
                    "nb_hits": response.nb_hits,
                },
            },
            indent=2,
            default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_algolia_semantic_search(query=query, index_name=index_name), indent=2
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "algolia_semantic_search",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
