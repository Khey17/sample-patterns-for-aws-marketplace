"""
module6/config/models.py
========================
Client configuration for Temporal Cloud and Amazon Bedrock.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TemporalConfig:
    """Connection settings for Temporal Cloud."""

    endpoint: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_ENDPOINT", "localhost:7233")
    )
    namespace: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_NAMESPACE", "devops-companion")
    )
    api_key: str | None = field(
        default_factory=lambda: os.getenv("TEMPORAL_API_KEY")
    )
    task_queue: str = "devops-companion"

    @property
    def mock_mode(self) -> bool:
        return not self.api_key


@dataclass
class EndpointConfig:
    """Settings for delegating to Module 1/2/3 HTTP endpoints."""

    module1_url: str = field(
        default_factory=lambda: os.getenv("MODULE1_URL", "http://localhost:8080")
    )
    module2_url: str = field(
        default_factory=lambda: os.getenv("MODULE2_URL", "http://localhost:8081")
    )
    module3_url: str = field(
        default_factory=lambda: os.getenv("MODULE3_URL", "http://localhost:8082")
    )


@dataclass
class DatadogConfig:
    """Settings for Datadog OTLP trace export."""

    api_key: str | None = field(
        default_factory=lambda: os.getenv("DD_API_KEY")
    )
    otlp_endpoint: str = field(
        default_factory=lambda: os.getenv(
            "DD_OTLP_ENDPOINT", "https://trace.agent.datadoghq.com:443"
        )
    )

    @property
    def mock_mode(self) -> bool:
        return not self.api_key
