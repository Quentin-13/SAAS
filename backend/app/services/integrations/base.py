"""
Base integration class for all external API clients.

Provides a unified interface with:
- Automatic mock mode controlled by ``settings.MOCK_APIS``
- Retry logic with exponential back-off via *tenacity*
- Structured logging via *structlog*
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


class IntegrationError(Exception):
    """Raised when an external API call fails after retries."""

    def __init__(self, service: str, message: str, status_code: int | None = None):
        self.service = service
        self.status_code = status_code
        super().__init__(f"[{service}] {message}")


class BaseIntegration:
    """Abstract base for every third-party integration client.

    Parameters
    ----------
    mock_mode:
        If *None* (the default), the value is read from ``settings.MOCK_APIS``.
        Pass an explicit ``True`` / ``False`` to override per-instance.
    """

    SERVICE_NAME: str = "base"

    def __init__(self, mock_mode: bool | None = None) -> None:
        self.mock_mode: bool = mock_mode if mock_mode is not None else settings.MOCK_APIS
        logger.info(
            "integration.init",
            service=self.SERVICE_NAME,
            mock_mode=self.mock_mode,
        )

    # ── Public entry-point ───────────────────────────────────────────────

    async def _make_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict:
        """Perform an HTTP request (or return mock data).

        Parameters
        ----------
        method:
            HTTP verb, e.g. ``"GET"``, ``"POST"``.
        url:
            Fully-qualified URL.
        **kwargs:
            Forwarded to ``httpx.AsyncClient.request`` (headers, json,
            params, data, etc.).

        Returns
        -------
        dict
            Parsed JSON response body.
        """
        if self.mock_mode:
            logger.debug(
                "integration.mock_request",
                service=self.SERVICE_NAME,
                method=method,
                url=url,
            )
            return self._mock_response(method, url, **kwargs)

        return await self._real_request(method, url, **kwargs)

    # ── Real HTTP call with retries ──────────────────────────────────────

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _real_request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> dict:
        """Execute the HTTP request with retries on transient errors."""
        logger.info(
            "integration.request",
            service=self.SERVICE_NAME,
            method=method,
            url=url,
        )
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                data: dict = response.json()
                logger.info(
                    "integration.response",
                    service=self.SERVICE_NAME,
                    status_code=response.status_code,
                    url=url,
                )
                return data
        except httpx.HTTPStatusError as exc:
            logger.error(
                "integration.http_error",
                service=self.SERVICE_NAME,
                status_code=exc.response.status_code,
                url=url,
                detail=exc.response.text[:500],
            )
            raise IntegrationError(
                service=self.SERVICE_NAME,
                message=f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error(
                "integration.timeout",
                service=self.SERVICE_NAME,
                url=url,
            )
            raise  # let tenacity retry
        except httpx.TransportError as exc:
            logger.error(
                "integration.transport_error",
                service=self.SERVICE_NAME,
                url=url,
                error=str(exc),
            )
            raise  # let tenacity retry

    # ── Mock hook (subclasses MUST override) ─────────────────────────────

    def _mock_response(self, method: str, url: str, **kwargs: Any) -> dict:
        """Return fake data for the given request.

        Subclasses **must** override this method.  The base implementation
        intentionally raises ``NotImplementedError``.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _mock_response"
        )
