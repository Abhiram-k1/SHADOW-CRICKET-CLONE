from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./shadow_cricket.db"
    STORAGE_BUCKET: str = "shadow-cricket-images"
    MODEL_VERSION: str = "v1.0.0"
    API_ENV: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()
