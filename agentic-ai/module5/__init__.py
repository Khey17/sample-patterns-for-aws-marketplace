# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5 — Domain-Specific Agent Applications
=============================================
Provides the Domain Adaptation Engine and three pre-built domain configurations
(customer engagement, geospatial intelligence, voice interaction) built on top
of Amazon Bedrock and LangGraph.

Public API
----------
create_domain_agent  : Factory function — build a ready-to-invoke DomainAgent.
DomainConfig         : Dataclass describing a domain's prompts, tools, and guardrails.
DomainAgent          : Thin wrapper around a compiled LangGraph ReAct agent.
"""

from module5.agent import create_domain_agent
from module5.engine.domain_adapter import DomainAgent, DomainConfig

__all__ = ["create_domain_agent", "DomainConfig", "DomainAgent"]
