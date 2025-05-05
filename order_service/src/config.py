from typing import Self

from pydantic import PostgresDsn, RedisDsn, model_validator, AmqpDsn
from pydantic_settings import BaseSettings

from src.constants import Environment


class Config(BaseSettings):
    DATABASE_URL: PostgresDsn
    DATABASE_ECHO: bool = False
    RABBITMQ_URL: AmqpDsn | None = None

    SITE_DOMAIN: str = "myapp.com"

    ENVIRONMENT: Environment = Environment.PRODUCTION

    # CORS_ORIGINS: list[str]
    # CORS_ORIGINS_REGEX: str | None = None
    # CORS_HEADERS: list[str]

    APP_VERSION: str = "1.0"

    TEST_DATABASE_URL: PostgresDsn | None = None


    @model_validator(mode='after')
    def check_test_database(self) -> Self:
        if self.ENVIRONMENT == Environment.TESTING and not self.TEST_DATABASE_URL:
            raise ValueError('Test database URL must be provided')
        return self



settings = Config()
