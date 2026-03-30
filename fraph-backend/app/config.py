from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fraph Backend"
    api_prefix: str = ""
    database_url: str = "sqlite:///./fraph.db"
    allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="FRAPH_",
        extra="ignore",
    )


settings = Settings()
