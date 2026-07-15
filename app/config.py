"""
Configuration module for the application.

This module loads all the environment variables from the .env file
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    """
    Converts environment variables into correct python types
    """

    #Postgres config
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    #Redis config
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    #FastAPI config
    API_HOST: str
    API_PORT: int
    DEBUG: bool

    #Cache config
    CACHE_TTL: int

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
        )

#Settings object to be reused
settings = Settings()