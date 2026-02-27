from abc import ABC
from typing import Any, Dict
from fastapi import HTTPException
import httpx

class GeocoderBase(ABC):
    def __init__(self, base_url: str):
        self.__base_url = base_url
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def _get(self, params: Dict[str, Any]):
        try:
            r = await self.__client.get(self.__base_url, params=params)
            r.raise_for_status()
            return r.json()

        except httpx.ReadTimeout:
            raise HTTPException(
                500,
                "Timeout connecting to geocoding API"
            )

        except httpx.HTTPStatusError as e:
            raise HTTPException(
                500,
                f"Geocoding API error: {e.response.status_code}"
            )

        except Exception:
            raise HTTPException(
                500,
                "Unexpected geocoding error"
            )
