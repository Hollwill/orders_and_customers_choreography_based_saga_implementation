from pydantic import PostgresDsn, RedisDsn, model_validator, AmqpDsn, MongoDsn
from pydantic_settings import BaseSettings

from src.constants import Environment


class Config(BaseSettings):
    DATABASE_URL: MongoDsn
    RABBITMQ_URL: AmqpDsn | None = None

    SITE_DOMAIN: str = "myapp.com"

    ENVIRONMENT: Environment = Environment.PRODUCTION

    # CORS_ORIGINS: list[str]
    # CORS_ORIGINS_REGEX: str | None = None
    # CORS_HEADERS: list[str]

    APP_VERSION: str = "1.0"


settings = Config()
