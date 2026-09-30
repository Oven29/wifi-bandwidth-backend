from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    DEFAULT_IMAGE_URL: str = "http://localhost:9000/media/telek.png"
    DEFAULT_VIDEO_URL: str = "http://localhost:9000/media/telek.mp4"

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "root"
    MINIO_SECRET_KEY: str = "Dina@0606"
    MINIO_BUCKET_NAME: str = "media"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"


settings = Settings()
