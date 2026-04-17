"""
file: weather_service.py

Service for retrieving data about current weather.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple
import httpx
from service.service_base import ServiceBase
from config.datasets import WEATHER_URL, WEATHER_API_KEY

@dataclass(frozen=True)
class _WeatherState:
    """
    Internal state of the weather service.
    """

    # List of (weather_station_id, weather_id, unix_timestamp, temperature, wind_speed, clouds)
    weather_rows: List[Tuple[int, int, int, float, float, int]]

class WeatherService(ServiceBase[_WeatherState]):
    """
    Service responsible for retrieving and caching weather data
    from an external API.
    """

    def __init__(self):
        super().__init__()

        # Predefined weather stations
        self.__stations: List[Tuple[int, float, float]] = [
            (0, 49.19482064819619, 16.60858970656206),          # Brno
            (2, 49.48751658862182, 16.66189404646401),          # Blansko
            (3, 48.95228981824652, 17.17734990243932)           # Hodonin
        ]

        self.__client = httpx.AsyncClient(
            headers={"User-Agent": "Routio/1.0 (academic project)"},
            timeout=10
        )

    async def _shutdown(self) -> None:
        """
        Gracefully releases service resources.
        """
        return await self.__client.aclose()

    async def reload(self) -> None:
        """
        Reloads weather data and replaces the internal cached state.
        """
        print("Loading weather cache")
        new_state = await self.__load_new_state()
        self._set_state(new_state)
       
    async def __load_new_state(self) -> _WeatherState:
        """
        Retrieves current weather data for all configured stations.

        Returns:
            New state containing weather records
        """
        weather_rows: List[Tuple[int, int, int, float, float, int]] = []
        for station in self.__stations:
            try:
                response = await self.__client.get(
                    WEATHER_URL,
                    params={
                        "lat": station[1],
                        "lon": station[2],
                        "appid": WEATHER_API_KEY
                    }
                )
                response.raise_for_status()
                data: Dict[str, Any] = response.json()

                # Extract relevant weather attributes
                weather_rows.append((
                    station[0],
                    data["weather"][0]["id"],
                    data["dt"] * 1000,
                    data["main"]["temp"],
                    data["wind"]["speed"],
                    data["clouds"]["all"]
                ))

            except Exception as e:
                print(f"Weather error for {station}: {e}")
                continue

        return _WeatherState(weather_rows=weather_rows)

    def get_stations(self) -> List[Tuple[int, float, float]]:
        """
        Returns the list of configured weather stations.

        Returns:
            List of tuples (station_id, latitude, longitude)
        """
        return self.__stations
    
    def get_weather_rows(self) -> List[Tuple[int, int, int, float, float, int]]:
        """
        Returns cached weather data.

        Returns:
            List of weather records in the format (weather_station_id,
            weather_id, unix_timestamp, temperature, wind_speed, clouds)
        """
        state = self._get_state()
        return state.weather_rows

# End of file weather_service.py
