from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    DEBUG: bool = False
    AUDIO_BASE_URL: str = "https://hs-platform.s3.us-east-005.backblazeb2.com"
    CORS_ORIGINS: str = "http://localhost:5173"
    B2_KEY_ID: str | None = None
    B2_APP_KEY: str | None = None
    B2_BUCKET: str = "hs-platform"
    class Config:
        env_file = ".env"
        extra = "ignore"

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if "sslmode=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}sslmode=require"
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
