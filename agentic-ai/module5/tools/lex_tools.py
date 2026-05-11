# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/lex_tools.py
============================
Amazon Lex V2 intent classification tool for the customer engagement domain.

Uses boto3 lexv2-runtime in live mode, falls back to mock data when
AGENT_MOCK_DOMAIN=true or when credentials / bot ID are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_lex_classify_intent

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def lex_classify_intent(
    text: str,
    bot_id: str = "",
    bot_alias_id: str = "TSTALIASID",
    locale_id: str = "en_US",
) -> str:
    """Classify customer intent using Amazon Lex V2.

    Sends the customer's text to a Lex V2 bot and returns the detected intent,
    confidence score, extracted slots, and sentiment analysis.

    Args:
        text: Customer message to classify (e.g. "I need help with my subscription").
        bot_id: Lex V2 bot ID. Falls back to AGENT_LEX_BOT_ID env var if empty.
        bot_alias_id: Lex V2 bot alias ID (default: TSTALIASID).
        locale_id: Locale for the bot (default: en_US).

    Returns:
        JSON string with Output_Envelope containing intent, confidence, slots, and sentiment.
    """
    if _is_mock():
        return json.dumps(
            mock_lex_classify_intent(
                text=text, bot_id=bot_id, bot_alias_id=bot_alias_id, locale_id=locale_id
            ),
            indent=2,
        )
    try:
        import boto3

        import uuid
        resolved_bot_id = bot_id or os.environ["AGENT_LEX_BOT_ID"]
        session_id = f"session-{uuid.uuid4().hex[:12]}"
        client = boto3.client("lexv2-runtime", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.recognize_text(
            botId=resolved_bot_id,
            botAliasId=bot_alias_id,
            localeId=locale_id,
            sessionId=session_id,
            text=text,
        )
        interpretations = response.get("interpretations", [])
        top = interpretations[0] if interpretations else {}
        return json.dumps(
            {
                "tool": "lex_classify_intent",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "input_text": text,
                    "bot_id": resolved_bot_id,
                    "locale_id": locale_id,
                    "session_id": response.get("sessionId", ""),
                    "intent": top.get("intent", {}),
                    "slots": top.get("intent", {}).get("slots", {}),
                    "sentiment": response.get("interpretations", [{}])[0].get(
                        "sentimentResponse", {}
                    ),
                },
            },
            indent=2,
            default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_lex_classify_intent(
                text=text, bot_id=bot_id, bot_alias_id=bot_alias_id, locale_id=locale_id
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "lex_classify_intent",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
