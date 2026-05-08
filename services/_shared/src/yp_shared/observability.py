from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider

def init_observability(service_name: str) -> None:
    """Initialize OpenTelemetry tracer and meter providers."""
    # This is a stub for the full OTLP setup. In a real app,
    # exporters would be configured based on env vars.
    trace.set_tracer_provider(TracerProvider())
    metrics.set_meter_provider(MeterProvider())
