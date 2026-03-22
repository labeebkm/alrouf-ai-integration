"""
Configuration management using pydantic-settings.
All values sourced from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Service
    service_name: str = "AL ROUF Quotation Microservice"
    service_port: int = 8000
    log_level: str = "INFO"

    # Security
    quotation_secret_key: str = "dev-secret-key-change-in-production"

    # Pricing
    price_list_path: str = "./data/price_list.json"
    default_currency: str = "USD"
    tax_rate: float = 0.05         # 5% VAT
    default_discount_pct: float = 0.0

    # Mock mode
    mock_mode: bool = False

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
