"""
file: geocoder_base.py

Defines abstract base class for geocoding services.
"""

from abc import ABC
from typing import Any, Dict
from fastapi import HTTPException
import httpx

class GeocoderBase(ABC):
    """
    Abstract base class for geocoding implementations.
    """
    def __init__(self, base_url: str):
        """
        Initializes geocoder with base API URL.

        Args:
            base_url: Base URL of the external geocoding service
        """
        self.__base_url = base_url

        # Shared asynchronous HTTP client
        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def _get(self, params: Dict[str, Any]):
        """
        Executes GET request to external geocoding API.

        Args:
            params: Query parameters sent to geocoding service.

        Returns:
            Parsed JSON response as dictionary
        """
        # Send request to geocoding API
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

# End of file geocoder_base.py
