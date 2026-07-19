"""Thread-local execution controls shared by every VedAstro import path."""
from __future__ import annotations

from contextlib import contextmanager
import contextvars


_TIMEOUT_OVERRIDE_SECONDS: contextvars.ContextVar[float | None] = contextvars.ContextVar(
    "vedastro_timeout_override_seconds",
    default=None,
)


def timeout_override_seconds() -> float | None:
    return _TIMEOUT_OVERRIDE_SECONDS.get()


@contextmanager
def temporary_timeout_seconds(seconds: float):
    token = _TIMEOUT_OVERRIDE_SECONDS.set(max(1.0, float(seconds)))
    try:
        yield
    finally:
        _TIMEOUT_OVERRIDE_SECONDS.reset(token)
