# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
module5/agent.py
================
Domain Agent Factory for Module 5.

This module provides a single factory function, ``create_domain_agent``,
that accepts a domain name (or a pre-built ``DomainConfig``) and returns
a fully configured ``DomainAgent`` ready for invocation.

FRAMEWORK: LangChain + LangGraph (consistent with Modules 2–4)
MODEL: Claude Sonnet 4.6 via Amazon Bedrock CRIS (Cross-Region Inference)
PATTERN: Domain-specialised ReAct agent via DomainAdapter
"""

from __future__ import annotations

from module5.engine.domain_adapter import DomainAdapter, DomainAgent, DomainConfig
from module5.config.models import get_chat_bedrock_model, SONNET_4_6, HAIKU_4_5
from module5.domains.customer import CUSTOMER_DOMAIN
from module5.domains.geospatial import GEOSPATIAL_DOMAIN
from module5.domains.voice import VOICE_DOMAIN
from module5.tools import ALL_TOOLS


# ---------------------------------------------------------------------------
# Domain registry
# ---------------------------------------------------------------------------

_DOMAIN_REGISTRY: dict[str, DomainConfig] = {
    "customer": CUSTOMER_DOMAIN,
    "geospatial": GEOSPATIAL_DOMAIN,
    "voice": VOICE_DOMAIN,
}

_VALID_DOMAIN_NAMES = list(_DOMAIN_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Agent Factory
# ---------------------------------------------------------------------------

def create_domain_agent(
    domain: str | DomainConfig,
    *,
    verbose: bool = True,
    region: str | None = None,
    streaming: bool = False,
    model_id: str = SONNET_4_6,
) -> DomainAgent:
    """
    Create a domain-specialised agent for Module 5.

    Accepts either a short domain name string or a fully constructed
    ``DomainConfig`` object.  The factory wires together the base Bedrock
    model, the shared tool registry, and the domain configuration via
    ``DomainAdapter.adapt``.

    Parameters
    ----------
    domain : str | DomainConfig
        Domain to specialise for.  Accepted string values are
        ``"customer"``, ``"geospatial"``, and ``"voice"``.
        Pass a ``DomainConfig`` directly to use a custom configuration.
    verbose : bool
        Print a configuration summary to stdout.  Default ``True`` for demos.
    region : str, optional
        AWS region override.  Falls back to the ``AWS_REGION`` /
        ``AWS_DEFAULT_REGION`` environment variables, then ``"us-east-1"``.
    model_id : str
        CRIS inference profile ID. Defaults to Sonnet 4.6 for domain reasoning.
        Use HAIKU_4_5 for lightweight/fast tasks.

    Returns
    -------
    DomainAgent
        Configured domain agent ready for ``.agent.invoke()``.

    Raises
    ------
    ValueError
        If *domain* is a string that is not in the registry.

    Example
    -------
    >>> from module5.agent import create_domain_agent
    >>> agent = create_domain_agent("customer")
    >>> result = agent.agent.invoke({
    ...     "messages": [("user", "Find me a monitoring tool")]
    ... })
    >>> print(result["messages"][-1].content)
    """
    # ── RESOLVE DOMAIN CONFIG ─────────────────────────────────────────────
    if isinstance(domain, str):
        if domain not in _DOMAIN_REGISTRY:
            raise ValueError(
                f"Unknown domain {domain!r}. Valid names: {_VALID_DOMAIN_NAMES}"
            )
        config = _DOMAIN_REGISTRY[domain]
    else:
        config = domain

    # ── BASE MODEL ────────────────────────────────────────────────────────
    base_model = get_chat_bedrock_model(region=region, streaming=streaming, model_id=model_id)

    # ── ADAPTER + AGENT ───────────────────────────────────────────────────
    adapter = DomainAdapter(ALL_TOOLS)
    domain_agent = adapter.adapt(base_model, config)

    # ── VERBOSE SUMMARY ───────────────────────────────────────────────────
    if verbose:
        guardrail_status = (
            f"guardrail_id={domain_agent.guardrail_id}"
            if domain_agent.guardrail_id
            else "no guardrail (mock/unavailable)"
        )
        print(f"  [Module 5 Domain Agent] {config.display_name}")
        print(f"  [Domain] {config.name}")
        print(f"  [Model] {model_id}")
        print(f"  [Tools] {len(config.tool_names)}: {', '.join(config.tool_names)}")
        print(f"  [Guardrails] {guardrail_status}")
        print()

    return domain_agent
