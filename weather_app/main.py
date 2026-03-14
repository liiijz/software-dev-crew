\"""
Weather API Service - Production Ready FastAPI Backend
========================================================
A production-ready FastAPI backend for Vue-based Weather SPA application.

This module serves as the main entry point and consolidates all application
components with proper Pydantic v2 compatibility, error handling, and
Python best practices.
"""

from fastapi import FastAPI, Request, Depends, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel, Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
from functools import lru_cache
import httpx
import logging
import sys
import time
import re


# =============================================================================
# Configuration Module
# =============================================================================

class Settings(BaseSettings):
    """
    Application settings class with Pydantic v2 compatibility.
    
    Attributes:
        app_name: Name of the application
        app_version: Version of the application
        debug: Debug mode flag
        weather_api_key: Weather API key
        weather_api_base_url: Base URL for weather API
        cors_origins: List of allowed CORS origins
        cache_ttl: Cache time-to-live in seconds
        log_level: Logging level
    """
    
    app_name: str = Field(default="Weather API Service", validation_alias="APP_NAME")
    app_version: str = Field(default="1.0.0", validation_alias="APP_VERSION")
    debug: bool = Field(default=False, validation_alias="DEBUG")
    
    # Weather API Configuration
    weather_api_key: str = Field(default="", validation_alias="WEATHER_API_KEY")
    weather_api_base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        validation_alias="WEATHER_API_BASE_URL"
    )
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:8080", "http://localhost:3000"],
        validation_alias="CORS_ORIGINS"
    )
    
    # Cache Configuration
    cache_ttl: int = Field(default=300, validation_alias="CACHE_TTL")
    
    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number range."""
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings instance
    """
    return Settings()


settings = get_settings()


# =============================================================================
# Logging Configuration
# =============================================================================

def setup_logging(level: Optional[str] = None) -> None:
    """
    Setup application logging.
    
    Args:
        level: Logging level (overrides config if provided)
    """
    log_level = level or settings.log_level
    
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    logging.getLogger("uvicorn").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("WARNING")
    
    logging.info(f"Logging configured with level: {log_level}")


# =============================================================================
# Custom Exceptions
# =============================================================================

class WeatherAPIException(HTTPException):
    """Custom exception for weather API related errors."""
    
    def __init__(
        self,
        detail: str = "Weather API error occurred",
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        headers: Optional[Dict[str, str]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class CityNotFoundException(WeatherAPIException):
    """Exception raised when city is not found."""
    
    def __init__(self, city_name: str):
        super().__init__(
            detail=f"City '{city_name}' not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class RateLimitException(WeatherAPIException):
    """Exception raised when API rate limit is exceeded."""
    
    def __init__(self, retry_after: Optional[int] = None):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        super().__init__(
            detail="API rate limit exceeded",
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers=headers
        )


class ValidationException(WeatherAPIException):
    """Exception raised when input validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class ServiceUnavailableException(WeatherAPIException):
    """Exception raised when external service is unavailable."""
    
    def __init__(self, service_name: str = "Weather Service"):
        super().__init__(
            detail=f"{service_name} is currently unavailable",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


# =============================================================================
# Exception Handlers
# =============================================================================

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for uncaught exceptions.
    
    Args:
        request: FastAPI request object
        exc: Exception object
        
    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "path": request.url.path
        }
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle validation errors.
    
    Args:
        request: FastAPI request object
        exc: RequestValidationError object
        
    Returns:
        JSONResponse: Error response with validation details
    """
    logger.warning(f"Validation error: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "path": request.url.path
        }
    )


# =============================================================================
# Data Models
# =============================================================================

class WeatherCondition(str, Enum):
    """Weather condition enum."""
    CLEAR = "Clear"
    CLOUDS = "Clouds"
    RAIN = "Rain"
    SNOW = "Snow"
    THUNDERSTORM = "Thunderstorm"
    DRIZZLE = "Drizzle"
    MIST = "Mist"
    FOG = "Fog"


class WeatherLocation(BaseModel):
    """Weather location model."""
    
    name: str = Field(..., description="City name")
    country: str = Field(..., description="Country code")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    timezone: Optional[int] = Field(None, description="Timezone offset in seconds")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "London",
                "country": "GB",
                "latitude": 51.5074,
                "longitude": -0.1278,
                "timezone": 0
            }
        }
    )


class WeatherData(BaseModel):
    """Current weather data model."""
    
    location: WeatherLocation
    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Feels like temperature")
    humidity: int = Field(..., description="Humidity percentage")
    pressure: int = Field(..., description="Pressure in hPa")
    wind_speed: float = Field(..., description="Wind speed in m/s")
    wind_direction: int = Field(..., description="Wind direction in degrees")
    condition: WeatherCondition = Field(..., description="Weather condition")
    description: str = Field(..., description="Weather description")
    visibility: int = Field(..., description="Visibility in meters")
    cloudiness: int = Field(..., description="Cloudiness percentage")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": {
                    "name": "London",
                    "country": "GB",
                    "latitude": 51.5074,
                    "longitude": -0.1278
                },
                "temperature": 15.5,
                "feels_like": 14.2,
                "humidity": 72,
                "pressure": 1013,
                "wind_speed": 3.5,
                "wind_direction": 180,
                "condition": "Clouds",
                "description": "Broken clouds",
                "visibility": 10000,
                "cloudiness": 75,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class ForecastHourly(BaseModel):
    """Hourly forecast data model."""
    
    timestamp: datetime
    temperature: float
    condition: WeatherCondition
    description: str
    humidity: int
    wind_speed: float
    precipitation_probability: Optional[float] = None


class ForecastDaily(BaseModel):
    """Daily forecast data model."""
    
    date: datetime
    temperature_max: float
    temperature_min: float
    condition: WeatherCondition
    description: str
    humidity: int
    wind_speed: float
    precipitation_probability: Optional[float] = None
    sunrise: Optional[datetime] = None
    sunset: Optional[datetime] = None


class ForecastData(BaseModel):
    """Forecast data model containing hourly and daily forecasts."""
    
    location: WeatherLocation
    hourly: List[ForecastHourly] = Field(default_factory=list)
    daily: List[ForecastDaily] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": {
                    "name": "London",
                    "country": "GB",
                    "latitude": 51.5074,
                    "longitude": -0.1278
                },
                "hourly": [],
                "daily": [],
                "generated_at": "2024-01-15T10:30:00Z"
            }
        }
    )


# =============================================================================
# Request/Response Schemas
# =============================================================================

class WeatherRequest(BaseModel):
    """Weather request schema."""
    
    city: str = Field(..., min_length=1, max_length=100, description="City name")
    country_code: Optional[str] = Field(None, min_length=2, max_length=2, description="Country code")
    units: str = Field(default="metric", description="Temperature units")
    
    @field_validator('city')
    @classmethod
    def validate_city(cls, v: str) -> str:
        """Validate city name."""
        if not v.strip():
            raise ValueError("City name cannot be empty")
        return v.strip()
    
    @field_validator('units')
    @classmethod
    def validate_units(cls, v: str) -> str:
        """Validate units parameter."""
        allowed_units = ["metric", "imperial", "standard"]
        if v not in allowed_units:
            raise ValueError(f"Units must be one of: {allowed_units}")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "city": "London",
                "country_code": "GB",
                "units": "metric"
            }
        }
    )


class CitySearchRequest(BaseModel):
    """City search request schema."""
    
    query: str = Field(..., min_length=1, max_length=100, description="City name")
    limit: int = Field(default=5, ge=1, le=20, description="Max results")
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query string."""
        if not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "London",
                "limit": 5
            }
        }
    )


class WeatherResponse(BaseModel):
    """Weather response schema."""
    
    success: bool = Field(default=True, description="Request success status")
    data: WeatherData = Field(..., description="Weather data")
    message: str = Field(default="Success", description="Response message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "location": {
                        "name": "London",
                        "country": "GB",
                        "latitude": 51.5074,
                        "longitude": -0.1278
                    },
                    "temperature": 15.5,
                    "feels_like": 14.2,
                    "humidity": 72,
                    "pressure": 1013,
                    "wind_speed": 3.5,
                    "wind_direction": 180,
                    "condition": "Clouds",
                    "description": "Broken clouds",
                    "visibility": 10000,
                    "cloudiness": 75,
                    "timestamp": "2024-01-15T10:30:00Z"
                },
                "message": "Success",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class ForecastResponse(BaseModel):
    """Forecast response schema."""
    
    success: bool = Field(default=True, description="Request success status")
    data: ForecastData = Field(..., description="Forecast data")
    message: str = Field(default="Success", description="Response message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": {
                    "location": {
                        "name": "London",
                        "country": "GB",
                        "latitude": 51.5074,
                        "longitude": -0.1278
                    },
                    "hourly": [],
                    "daily": [],
                    "generated_at": "2024-01-15T10:30:00Z"
                },
                "message": "Success",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    success: bool = Field(default=False, description="Request success status")
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
    path: Optional[str] = Field(None, description="Request path")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": False,
                "error": "CityNotFound",
                "detail": "City 'InvalidCity' not found",
                "path": "/api/weather",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    uptime: float = Field(..., description="Service uptime in seconds")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "uptime": 3600.5,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }
    )


class CitySearchResponse(BaseModel):
    """City search response schema."""
    
    success: bool = Field(default=True, description="Request success status")
    data: List[WeatherLocation] = Field(default_factory=list, description="Matching locations")
    count: int = Field(..., description="Number of results")
    message: str = Field(default="Success", description="Response message")
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "success": True,
                "data": [
                    {
                        "name": "London",
                        "country": "GB",
                        "latitude": 51.5074,
                        "longitude": -0.1278
                    }
                ],
                "count": 1,
                "message": "Success"
            }
        }
    )


# =============================================================================
# Cache Service
# =============================================================================

class CacheService:
    """
    Cache service for storing and retrieving weather data.
    
    Attributes:
        cache: In-memory cache dictionary
        ttl: Default time-to-live in seconds
    """
    
    def __init__(self, ttl: int = None):
        """
        Initialize cache service.
        
        Args:
            ttl: Default cache TTL in seconds
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl or settings.cache_ttl
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """
        Generate cache key from parameters.
        
        Args:
            prefix: Key prefix
            **kwargs: Key parameters
            
        Returns:
            str: Generated cache key
        """
        params = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None)
        return f"{prefix}:{params}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if datetime.now(timezone.utc) > entry["expires_at"]:
            del self.cache[key]
            return None
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        ttl = ttl or self.ttl
        self.cache[key] = {
            "value": value,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl)
        }
        logger.debug(f"Cached key: {key}, TTL: {ttl}s")
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_weather_key(self, city: str, country_code: Optional[str], units: str) -> str:
        """
        Generate weather cache key.
        
        Args:
            city: City name
            country_code: Country code
            units: Temperature units
            
        Returns:
            str: Cache key
        """
        return self._generate_key("weather", city=city, country=country_code, units=units)
    
    def get_forecast_key(self, city: str, country_code: Optional[str], units: str) -> str:
        """
        Generate forecast cache key.
        
        Args:
            city: City name
            country_code: Country code
            units: Temperature units
            
        Returns:
            str: Cache key
        """
        return self._generate_key("forecast", city=city, country=country_code, units=units)


# Global cache instance
cache_service = CacheService()


# =============================================================================
# Weather Service
# =============================================================================

class WeatherService:
    """
    Weather service for fetching and processing weather data.
    
    Attributes:
        api_key: Weather API key
        base_url: Weather API base URL
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize weather service.
        
        Args:
            api_key: Weather API key
            base_url: Weather API base URL
            timeout: Request timeout
        """
        self.api_key = api_key or settings.weather_api_key
        self.base_url = base_url or settings.weather_api_base_url
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """
        Get or create HTTP client.
        
        Returns:
            httpx.AsyncClient: HTTP client instance
        """
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self) -> None:
        """Close HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    def _parse_weather_condition(self, condition_id: int) -> WeatherCondition:
        """
        Parse weather condition from condition ID.
        
        Args:
            condition_id: Weather condition ID from API
            
        Returns:
            WeatherCondition: Parsed weather condition
        """
        if 200 <= condition_id < 300:
            return WeatherCondition.THUNDERSTORM
        elif 300 <= condition_id < 400:
            return WeatherCondition.DRIZZLE
        elif 500 <= condition_id < 600:
            return WeatherCondition.RAIN
        elif 600 <= condition_id < 700:
            return WeatherCondition.SNOW
        elif 700 <= condition_id < 800:
            return WeatherCondition.MIST
        elif condition_id == 800:
            return WeatherCondition.CLEAR
        else:
            return WeatherCondition.CLOUDS
    
    def _parse_weather_data(self, data: Dict[str, Any]) -> WeatherData:
        """
        Parse weather data from API response.
        
        Args:
            data: Raw API response data
            
        Returns:
            WeatherData: Parsed weather data
        """
        location = WeatherLocation(
            name=data["name"],
            country=data["sys"]["country"],
            latitude=data["coord"]["lat"],
            longitude=data["coord"]["lon"],
            timezone=data.get("timezone")
        )
        
        weather = data["weather"][0]
        main = data["main"]
        wind = data["wind"]
        
        return WeatherData(
            location=location,
            temperature=main["temp"],
            feels_like=main["feels_like"],
            humidity=main["humidity"],
            pressure=main["pressure"],
            wind_speed=wind["speed"],
            wind_direction=wind.get("deg", 0),
            condition=self._parse_weather_condition(weather["id"]),
            description=weather["description"],
            visibility=data.get("visibility", 10000),
            cloudiness=data["clouds"]["all"],
            timestamp=datetime.fromtimestamp(data["dt"], tz=timezone.utc)
        )
    
    async def get_current_weather(
        self,
        city: str,
        country_code: Optional[str] = None,
        units: str = "metric"
    ) -> WeatherData:
        """
        Get current weather for a city.
        
        Args:
            city: City name
            country_code: Optional country code
            units: Temperature units
            
        Returns:
            WeatherData: Current weather data
            
        Raises:
            CityNotFoundException: If city is not found
            WeatherAPIException: If API request fails
            ServiceUnavailableException: If service is unavailable
        """
        if not self.api_key:
            raise WeatherAPIException(
                detail="Weather API key not configured",
                status_code=500
            )
        
        client = await self._get_client()
        
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units
        }
        
        if country_code:
            params["q"] = f"{city},{country_code}"
        
        try:
            response = await client.get(
                f"{self.base_url}/weather",
                params=params
            )
            
            if response.status_code == 404:
                raise CityNotFoundException(city)
            elif response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                raise RateLimitException(
                    retry_after=int(retry_after) if retry_after else None
                )
            elif response.status_code != 200:
                raise WeatherAPIException(
                    detail=f"Weather API error: {response.status_code}",
                    status_code=response.status_code
                )
            
            data = response.json()
            return self._parse_weather_data(data)
            
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching weather for {city}")
            raise ServiceUnavailableException("Weather API")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise WeatherAPIException(detail="Failed to connect to weather service")
    
    async def get_forecast(
        self,
        city: str,
        country_code: Optional[str] = None,
        units: str = "metric",
        days: int = 5
    ) -> ForecastData:
        """
        Get weather forecast for a city.
        
        Args:
            city: City name
            country_code: Optional country code
            units: Temperature units
            days: Number of days for forecast
            
        Returns:
            ForecastData: Forecast data
            
        Raises:
            CityNotFoundException: If city is not found
            WeatherAPIException: If API request fails
        """
        if not self.api_key:
            raise WeatherAPIException(
                detail="Weather API key not configured",
                status_code=500
            )
        
        client = await self._get_client()
        
        params = {
            "q": city,
            "appid": self.api_key,
            "units": units,
            "cnt": min(days * 8, 40)
        }
        
        if country_code:
            params["q"] = f"{city},{country_code}"
        
        try:
            response = await client.get(
                f"{self.base_url}/forecast",
                params=params
            )
            
            if response.status_code == 404:
                raise CityNotFoundException(city)
            elif response.status_code != 200:
                raise WeatherAPIException(
                    detail=f"Forecast API error: {response.status_code}",
                    status_code=response.status_code
                )
            
            data = response.json()
            return self._parse_forecast_data(data, days)
            
        except httpx.TimeoutException:
            logger.error(f"Timeout fetching forecast for {city}")
            raise ServiceUnavailableException("Forecast API")
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            raise WeatherAPIException(detail="Failed to connect to forecast service")
    
    def _parse_forecast_data(
        self,
        data: Dict[str, Any],
        days: int
    ) -> ForecastData:
        """
        Parse forecast data from API response.
        
        Args:
            data: Raw API response data
            days: Number of days
            
        Returns:
            ForecastData: Parsed forecast data
        """
        location = WeatherLocation(
            name=data["city"]["name"],
            country=data["city"]["country"],
            latitude=data["city"]["coord"]["lat"],
            longitude=data["city"]["coord"]["lon"]
        )
        
        hourly = []
        daily_data = {}
        
        for item in data["list"]:
            timestamp = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            weather = item["weather"][0]
            main = item["main"]
            wind = item["wind"]
            
            hourly_forecast = ForecastHourly(
                timestamp=timestamp,
                temperature=main["temp"],
                condition=self._parse_weather_condition(weather["id"]),
                description=weather["description"],
                humidity=main["humidity"],
                wind_speed=wind["speed"],
                precipitation_probability=item.get("pop", 0)
            )
            hourly.append(hourly_forecast)
            
            date_key = timestamp.date()
            if date_key not in daily_data:
                daily_data[date_key] = {
                    "temps": [],
                    "items": []
                }
            daily_data[date_key]["temps"].append(main["temp"])
            daily_data[date_key]["items"].append(item)
        
        daily = []
        for date, data_dict in list(daily_data.items())[:days]:
            items = data_dict["items"]
            temps = data_dict["temps"]
            main_item = items[0]
            
            daily_forecast = ForecastDaily(
                date=datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc),
                temperature_max=max(temps),
                temperature_min=min(temps),
                condition=self._parse_weather_condition(main_item["weather"][0]["id"]),
                description=main_item["weather"][0]["description"],
                humidity=main_item["main"]["humidity"],
                wind_speed=main_item["wind"]["speed"],
                precipitation_probability=max(item.get("pop", 0) for item in items)
            )
            daily.append(daily_forecast)
        
        return ForecastData(
            location=location,
            hourly=hourly,
            daily=daily,
            generated_at=datetime.now(timezone.utc)
        )
    
    async def search_cities(
        self,
        query: str,
        limit: int = 5
    ) -> List[WeatherLocation]:
        """
        Search for cities by name.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List[WeatherLocation]: List of matching locations
        """
        if not self.api_key:
            logger.warning("API key not configured for city search")
            return []
        
        client = await self._get_client()
        
        params = {
            "q": query,
            "appid": self.api_key,
            "limit": limit
        }
        
        try:
            response = await client.get(
                f"{self.base_url}/geo/1.0/direct",
                params=params
            )
            
            if response.status_code != 200:
                logger.warning(f"City search failed: {response.status_code}")
                return []
            
            data = response.json()
            locations = []
            
            for item in data:
                location = WeatherLocation(
                    name=item["name"],
                    country=item.get("country", "Unknown"),
                    latitude=item["lat"],
                    longitude=item["lon"]
                )
                locations.append(location)
            
            return locations
            
        except Exception as e:
            logger.error(f"City search error: {str(e)}")
            return []


# =============================================================================
# API Routes
# =============================================================================

router = APIRouter(prefix="/api/v1", tags=["Weather API"])

_weather_service: Optional[WeatherService] = None
_startup_time: Optional[float] = None


def get_weather_service() -> WeatherService:
    """
    Get weather service instance.
    
    Returns:
        WeatherService: Weather service instance
    """
    global _weather_service
    if _weather_service is None:
        _weather_service = WeatherService()
    return _weather_service


def get_uptime() -> float:
    """
    Get application uptime in seconds.
    
    Returns:
        float: Uptime in seconds
    """
    global _startup_time
    if _startup_time is None:
        _startup_time = time.time()
    return time.time() - _startup_time


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check API health status"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        uptime=get_uptime()
    )


@router.get(
    "/weather",
    response_model=WeatherResponse,
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    },
    summary="Get Current Weather",
    description="Get current weather data for a specified city"
)
async def get_weather(
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    country_code: Optional[str] = Query(None, min_length=2, max_length=2, description="Country code"),
    units: str = Query("metric", description="Temperature units"),
    service: WeatherService = Depends(get_weather_service)
) -> WeatherResponse:
    """
    Get current weather for a city.
    
    Args:
        city: City name
        country_code: Optional country code (ISO 3166-1 alpha-2)
        units: Temperature units (metric, imperial, standard)
        service: Weather service dependency
        
    Returns:
        WeatherResponse: Current weather data
        
    Raises:
        CityNotFoundException: If city is not found
        WeatherAPIException: If API request fails
    """
    cache_key = cache_service.get_weather_key(city, country_code, units)
    
    cached_data = cache_service.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for {city}")
        return WeatherResponse(
            success=True,
            data=cached_data,
            message="Data from cache"
        )
    
    try:
        weather_data = await service.get_current_weather(
            city=city,
            country_code=country_code,
            units=units
        )
        
        cache_service.set(cache_key, weather_data)
        
        return WeatherResponse(
            success=True,
            data=weather_data,
            message="Success"
        )
        
    except CityNotFoundException as e:
        logger.warning(f"City not found: {city}")
        raise e
    except RateLimitException as e:
        logger.warning(f"Rate limit exceeded for {city}")
        raise e
    except ServiceUnavailableException as e:
        logger.error(f"Service unavailable: {str(e)}")
        raise e
    except WeatherAPIException as e:
        logger.error(f"Weather API error: {str(e)}")
        raise e


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    responses={
        404: {"model": ErrorResponse, "description": "City not found"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Service unavailable"}
    },
    summary="Get Weather Forecast",
    description="Get weather forecast for a specified city"
)
async def get_forecast(
    city: str = Query(..., min_length=1, max_length=100, description="City name"),
    country_code: Optional[str] = Query(None, min_length=2, max_length=2, description="Country code"),
    units: str = Query("metric", description="Temperature units"),
    days: int = Query(5, ge=1, le=16, description="Number of days"),
    service: WeatherService = Depends(get_weather_service)
) -> ForecastResponse:
    """
    Get weather forecast for a city.
    
    Args:
        city: City name
        country_code: Optional country code
        units: Temperature units
        days: Number of days for forecast (1-16)
        service: Weather service dependency
        
    Returns:
        ForecastResponse: Forecast data
    """
    cache_key = cache_service.get_forecast_key(city, country_code, units)
    
    cached_data = cache_service.get(cache_key)
    if cached_data:
        logger.info(f"Cache hit for forecast {city}")
        return ForecastResponse(
            success=True,
            data=cached_data,
            message="Data from cache"
        )
    
    try:
        forecast_data = await service.get_forecast(
            city=city,
            country_code=country_code,
            units=units,
            days=days
        )
        
        cache_service.set(cache_key, forecast_data, ttl=600)
        
        return ForecastResponse(
            success=True,
            data=forecast_data,
            message="Success"
        )
        
    except CityNotFoundException as e:
        logger.warning(f"City not found: {city}")
        raise e
    except WeatherAPIException as e:
        logger.error(f"Weather API error: {str(e)}")
        raise e


@router.get(
    "/search",
    response_model=CitySearchResponse,
    summary="Search Cities",
    description="Search for cities by name"
)
async def search_cities(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Max results"),
    service: WeatherService = Depends(get_weather_service)
) -> CitySearchResponse:
    """
    Search for cities by name.
    
    Args:
        q: Search query
        limit: Maximum number of results
        service: Weather service dependency
        
    Returns:
        CitySearchResponse: List of matching cities
    """
    locations = await service.search_cities(query=q, limit=limit)
    
    return CitySearchResponse(
        success=True,
        data=locations,
        count=len(locations),
        message="Success" if locations else "No cities found"
    )


# =============================================================================
# Main Application
# =============================================================================

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Args:
        app: FastAPI application
    """
    global _startup_time
    _startup_time = time.time()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    yield
    logger.info("Shutting down application")
    weather_service = get_weather_service()
    if weather_service:
        await weather_service.close()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Weather API Service for Vue-based SPA application",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(router)


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    
    Returns:
        dict: Welcome message
    """
    return {
        "message": "Welcome to Weather API Service",
        "version": settings.app_version,
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )