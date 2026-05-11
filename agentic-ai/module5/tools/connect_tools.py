# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/tools/connect_tools.py
================================
Amazon Connect escalation tool for the customer engagement domain.

Returns a structured escalation ticket. In live mode, uses boto3 connect
start_task_contact to create a real contact. Falls back to mock data when
AGENT_MOCK_DOMAIN=true or when credentials / instance ID are unavailable.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from langchain_core.tools import tool

from module5.mock.domain_mocks import mock_connect_escalate_to_human

def _is_mock() -> bool:
    return os.getenv("AGENT_MOCK_DOMAIN", "true").lower() == "true"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


@tool
def connect_escalate_to_human(
    reason: str,
    customer_id: str = "unknown",
    priority: str = "NORMAL",
) -> str:
    """Escalate conversation to a human agent via Amazon Connect.

    Creates an escalation ticket and queues the customer for a human agent.
    Priority can be NORMAL or HIGH. Returns ticket ID, queue, and estimated
    wait time so the agent can inform the customer.

    Args:
        reason: Why escalation is needed (e.g. "billing dispute requires manual review").
        customer_id: Customer identifier for routing (default: "unknown").
        priority: Escalation priority — NORMAL or HIGH (default: NORMAL).

    Returns:
        JSON string with Output_Envelope containing ticket ID, queue, and wait estimate.
    """
    if _is_mock():
        return json.dumps(
            mock_connect_escalate_to_human(
                reason=reason, customer_id=customer_id, priority=priority
            ),
            indent=2,
        )
    try:
        import boto3

        instance_id = os.environ["AGENT_CONNECT_INSTANCE_ID"]
        contact_flow_id = os.environ["AGENT_CONNECT_CONTACT_FLOW_ID"]
        client = boto3.client("connect", region_name=os.getenv("AWS_REGION", "us-east-1"))
        response = client.start_task_contact(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id,
            Name=f"Escalation-{customer_id}",
            Description=reason,
            Attributes={
                "customer_id": customer_id,
                "priority": priority,
                "reason": reason,
            },
        )
        return json.dumps(
            {
                "tool": "connect_escalate_to_human",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {
                    "ticket_id": response.get("ContactId", ""),
                    "customer_id": customer_id,
                    "status": "QUEUED",
                    "priority": priority,
                    "reason": reason,
                    "contact_id": response.get("ContactId", ""),
                    "channel": "TASK",
                },
            },
            indent=2,
            default=str,
        )
    except (ImportError, KeyError):
        return json.dumps(
            mock_connect_escalate_to_human(
                reason=reason, customer_id=customer_id, priority=priority
            ),
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {
                "tool": "connect_escalate_to_human",
                "timestamp": _timestamp(),
                "mock_mode": False,
                "data": {"error": str(e)},
            },
            indent=2,
        )
