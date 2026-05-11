# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/personalize_tools.py
=====================================
Amazon Personalize recommendations tool for the customer engagement domain.

Uses boto3 personalize-runtime in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when credentials / campaign ARN are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_personalize_get_recommendations

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def personalize_get_recommendations(user_id: str, num_results: int = 5) -> str:
    """Get personalized product recommendations from Amazon Personalize.

    Calls the Personalize campaign specified by AGENT_PERSONALIZE_CAMPAIGN_ARN
    to retrieve ranked item recommendations for the given user.

    Args:
        user_id: Unique identifier for the customer (e.g. "user-8472").
        num_results: Number of recommendations to return (default: 5).

    Returns:
        JSON string with Output_Envelope containing recommended item IDs and scores.
    """
    if _is_mock():
        return json.dumps(
            mock_personalize_get_recommendations(user_id=user_id, num_results=num_results),
            indent=2,
        )
    try:
        import boto3

        campaign_arn = os.environ["AGENT_PERSONALIZE_CAMPAIGN_ARN"]
        client = boto3.client("personalize-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.get_recommendations(
            campaignArn=campaign_arn,
            userId=user_id,
            numResults=num_results,
        )
        return json.dumps(
            {
                "tool": "personalize_get_recommendations",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "user_id": user_id,
                    "recommendation_id": response.get("recommendationId", ""),
                    "items": response.get("itemList", []),
                },
            },
            indent=2,
            default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_personalize_get_recommendations(user_id=user_id, num_results=num_results),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "personalize_get_recommendations",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
