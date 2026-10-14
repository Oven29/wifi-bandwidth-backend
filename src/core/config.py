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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://localhost:6379/0"

    db: DBSettings = Field(default_factory=DBSettings)
    minio: MinioSettings = Field(default_factory=MinioSettings)


settings = Settings()
