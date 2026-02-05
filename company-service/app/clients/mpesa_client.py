"""M-PESA API client with timeouts, retries, and idempotent-friendly calls."""

import logging
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import get_settings

logger = logging.getLogger(__name__)


class MpesaClientError(Exception):
    """M-PESA API error."""

    def __init__(self, message: str, status_code: int | None = None, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class MpesaClient:
    """
    Async client for M-PESA API.
    - Timeouts on all requests
    - Retries with exponential backoff (max 3)
    - Idempotent: POST /apps and PATCH /apps are used as specified
    """

    def __init__(
        self,
        base_url: str | None = None,
        callback_url: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ):
        settings = get_settings()
        self.base_url = (base_url or settings.mpesa_base_url).rstrip("/")
        self.callback_url = callback_url or settings.company_callback_url
        self._timeout = timeout if timeout is not None else settings.http_timeout_seconds
        self._max_retries = max_retries if max_retries is not None else settings.http_max_retries

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self._timeout,
            headers={"Content-Type": "application/json"},
        )

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_app(self, name: str) -> dict[str, Any]:
        """
        POST {MPESA_BASE_URL}/apps
        Body: name, callback_url
        Returns: name, account_number, api_key, callback_url, created_at (from response).
        """
        async with self._client() as client:
            payload = {
                "name": name,
                "callback_url": self.callback_url,
            }
            response = await client.post("/apps", json=payload)
            if response.status_code >= 400:
                raise MpesaClientError(
                    f"M-PESA create app failed: {response.text}",
                    status_code=response.status_code,
                    body=response.text,
                )
            data = response.json()
            if not isinstance(data, dict):
                raise MpesaClientError("M-PESA create app returned non-JSON or non-object")
            return data

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def update_app(
        self,
        api_key: str,
        name: str,
    ) -> dict[str, Any]:
        """
        PATCH {MPESA_BASE_URL}/apps
        Headers: Authorization: Bearer <api_key>
        Body: name, callback_url
        """
        async with self._client() as client:
            payload = {
                "name": name,
                "callback_url": self.callback_url,
            }
            response = await client.patch(
                "/apps",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code >= 400:
                raise MpesaClientError(
                    f"M-PESA update app failed: {response.text}",
                    status_code=response.status_code,
                    body=response.text,
                )
            return response.json() if response.content else {}

    @retry(
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def create_paybill(
        self,
        api_key: str,
        name: str,
        consumer_key: str,
        consumer_secret: str,
        business_short_code: str,
        passkey: str,
        initiator_name: str,
        security_credential: str,
        environment: str,
    ) -> dict[str, Any]:
        """
        POST {MPESA_BASE_URL}/paybills
        Headers: Authorization: Bearer <company.api_key>
        Body: same as request (name, consumer_key, consumer_secret, etc.)
        Returns: credential_id, name, business_short_code, environment, created_at, updated_at
        """
        async with self._client() as client:
            payload = {
                "name": name,
                "consumer_key": consumer_key,
                "consumer_secret": consumer_secret,
                "business_short_code": business_short_code,
                "passkey": passkey,
                "initiator_name": initiator_name,
                "security_credential": security_credential,
                "environment": environment,
            }
            response = await client.post(
                "/paybills",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
            if response.status_code >= 400:
                raise MpesaClientError(
                    f"M-PESA create paybill failed: {response.text}",
                    status_code=response.status_code,
                    body=response.text,
                )
            data = response.json()
            if not isinstance(data, dict):
                raise MpesaClientError("M-PESA create paybill returned non-JSON or non-object")
            return data
