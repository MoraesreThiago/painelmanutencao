from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


class BackendApiError(Exception):
    """Represents a failed request to the existing FastAPI backend."""


@dataclass
class BackendApiClient:
    base_url: str
    timeout_seconds: float = 15.0

    async def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        async with httpx.AsyncClient(base_url=f"{self.base_url.rstrip('/')}/", timeout=self.timeout_seconds) as client:
            try:
                response = await client.request(
                    method.upper(),
                    path.lstrip("/"),
                    headers=headers,
                    params=params,
                    json=payload,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                detail = "Unexpected API error."
                try:
                    detail = exc.response.json().get("detail", detail)
                except Exception:
                    detail = exc.response.text or detail
                raise BackendApiError(detail) from exc
            except httpx.HTTPError as exc:
                raise BackendApiError(f"Nao foi possivel acessar a API em {self.base_url}.") from exc

        if not response.text:
            return None
        return response.json()

