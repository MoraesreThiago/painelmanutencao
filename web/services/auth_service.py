from __future__ import annotations

from dataclasses import dataclass

from services.api_client import BackendApiClient
from services.config import settings


@dataclass
class AuthService:
    api_client: BackendApiClient

    async def login(self, email: str, password: str) -> dict:
        return await self.api_client.request("POST", "/auth/login", payload={"email": email, "password": password})

    async def current_user(self, token: str) -> dict:
        return await self.api_client.request("GET", "/auth/me", token=token)


auth_service = AuthService(
    api_client=BackendApiClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
)


