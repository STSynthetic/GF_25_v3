from __future__ import annotations


class GoFlowError(Exception):
    """Base error for GoFlow client operations."""


class GoFlowRetryableError(GoFlowError):
    """Retryable error (typically 5xx or transient network)."""


class GoFlowAuthError(GoFlowError):
    """Authentication/authorization related error (401/403)."""


class GoFlowNotFound(GoFlowError):
    """Resource not found (404)."""


class GoFlowServerError(GoFlowRetryableError):
    """Server-side error (5xx)."""


class GoFlowClientError(GoFlowError):
    """Client-side error (4xx not covered by specialized types)."""
