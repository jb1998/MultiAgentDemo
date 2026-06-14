from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "multiAgent Demo"
    database_url: str = "sqlite+aiosqlite:///./storage.db"
    secret_key: str = "dev-secret-key-change-in-production"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit: str = "100/minute"
    access_token_expire_minutes: int = 60

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    class Config:
        env_file = ".env"


settings = Settings()
