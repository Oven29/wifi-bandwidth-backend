from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DB_", env_file=".env", extra="ignore")

    host: str
    port: int
    user: str
    password: str
    name: str

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class MinioSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MINIO_", env_file=".env", extra="ignore")

    endpoint: str
    access_key: str
    secret_key: str
    bucket_name: str


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="REDIS_", env_file=".env", extra="ignore"
    )

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    redis: RedisSettings = Field(default_factory=RedisSettings)
    db: DBSettings = Field(default_factory=DBSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)

    @property
    def REDIS_URL(self) -> str:
        return self.redis.url


settings = Settings()
