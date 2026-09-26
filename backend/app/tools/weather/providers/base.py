import abc
from app.tools.weather.schemas import WeatherOutput


class BaseWeatherProvider(abc.ABC):
    """
    Abstract interface for Weather data providers.
    Allows seamlessly swapping Open-Meteo, OpenWeatherMap, WeatherAPI, etc.
    """

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        pass

    @abc.abstractmethod
    async def fetch_weather(
        self, city: str, days: int = 1, unit: str = "celsius"
    ) -> WeatherOutput:
        """
        Fetch real-time and forecast weather data for a city.
        """
        pass
