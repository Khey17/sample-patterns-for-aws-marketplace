"""
orchestration/tracing.py
=========================
OpenTelemetry setup for Temporal workflows.

Configures a TracerProvider that exports spans via OTLP/gRPC to the
Datadog Agent (localhost:4317). Returns a TracingInterceptor that the
Temporal client and worker use to instrument all workflow/activity calls.
"""

from __future__ import annotations

from temporalio.contrib.opentelemetry import TracingInterceptor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

_interceptor: TracingInterceptor | None = None


def get_tracing_interceptor(
    service_name: str = "devops-companion",
    otlp_endpoint: str = "http://localhost:4317",
) -> TracingInterceptor:
    """Configure OTel and return a reusable TracingInterceptor."""
    global _interceptor
    if _interceptor is not None:
        return _interceptor

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
    )
    trace.set_tracer_provider(provider)

    _interceptor = TracingInterceptor()
    return _interceptor
