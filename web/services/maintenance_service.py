from __future__ import annotations

from dataclasses import dataclass

from services.api_client import BackendApiClient
from services.config import settings


@dataclass
class MaintenanceService:
    api_client: BackendApiClient

    async def dashboard(self, token: str, area_id: str | None = None) -> dict:
        params = {"area_id": area_id} if area_id else None
        return await self.api_client.request("GET", "/dashboard", token=token, params=params)

    async def mechanical_overview(self, token: str) -> dict:
        return await self.api_client.request("GET", "/mechanical/overview", token=token)

    async def list_equipments(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/equipments", token=token)

    async def list_motors(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/motors", token=token)

    async def list_instruments(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/instruments", token=token)

    async def list_movements(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/movements", token=token)

    async def list_collaborators(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/collaborators", token=token)

    async def list_motor_replacements(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/motor-replacements", token=token)

    async def list_burned_motors(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/burned-motors", token=token)

    async def list_external_service_orders(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/external-service-orders", token=token)

    async def list_instrument_replacements(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/instrument-replacements", token=token)

    async def list_instrument_service_requests(self, token: str) -> list[dict]:
        return await self.api_client.request("GET", "/instrument-service-requests", token=token)


maintenance_service = MaintenanceService(
    api_client=BackendApiClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
)

