"""
orchestration/config.py
========================
Connection configuration for Temporal dev server or Temporal Cloud.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class TemporalConnectionConfig:
    """Temporal connection settings.

    No API key  -> dev server mode: localhost:7233, namespace "default", no TLS.
    API key set -> Cloud mode: custom endpoint, namespace, TLS enabled.
    """

    endpoint: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_ENDPOINT", "localhost:7233")
    )
    namespace: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_NAMESPACE", "default")
    )
    api_key: str | None = field(
        default_factory=lambda: os.getenv("TEMPORAL_API_KEY")
    )
    task_queue: str = field(
        default_factory=lambda: os.getenv("TEMPORAL_TASK_QUEUE", "devops-companion")
    )
    module2_url: str = field(
        default_factory=lambda: os.getenv("MODULE2_URL", "http://localhost:8081")
    )
    module3_url: str = field(
        default_factory=lambda: os.getenv("MODULE3_URL", "http://localhost:8082")
    )

    @property
    def use_tls(self) -> bool:
        return self.api_key is not None

    @property
    def is_cloud(self) -> bool:
        return self.api_key is not None

    @property
    def is_dev_server(self) -> bool:
        return self.api_key is None
