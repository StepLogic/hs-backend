from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str 
    SECRET_KEY: str
    DEBUG: bool = False
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    B2_KEY_ID: str = ""
    B2_APP_KEY: str = ""
    B2_BUCKET: str = "hs-platform"
    S3_ENDPOINT: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "hs-platform"
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    FRONTEND_URL: str = "http://localhost:5173"
    # Comma-separated. Credentialed CORS forbids a wildcard, so the origins allowed
    # to call this API have to be named.
    ALLOWED_ORIGINS: str = ""
    # hs-admin is deployed on Vercel, which mints a fresh hostname for every preview
    # deploy. Listing them one by one is how production ended up locked out, so the
    # project's own Vercel hostnames are matched by pattern instead. Scoped to this
    # project on purpose — `.*\.vercel\.app` would let any Vercel site make
    # credentialed calls against this API.
    ALLOWED_ORIGIN_REGEX: str = r"https://hs-(admin|platform)[a-z0-9-]*\.vercel\.app"
    # This service's own public URL. The Google OAuth redirect_uri must point at the
    # callback route on *this* API, not at the frontend, and must match byte-for-byte
    # between the authorize request and the token exchange.
    BACKEND_URL: str = "http://localhost:8000"
    class Config:
        env_file = ".env"
        extra = "ignore"
    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("sqlite"):
            return url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if "sslmode=" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}sslmode=require"
        return url


settings = Settings()
