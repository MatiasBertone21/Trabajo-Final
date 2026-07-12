from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Automation Lab API"
    version: str = "0.2"
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()