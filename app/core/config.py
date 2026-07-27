from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str
    API_V1_STR: str
    SECRET_KEY: str
    DATABASE_URL: str
    REDIS_URL: str
    GOOGLE_CLIENT_ID: str = ""

    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_MINUTES: int

    LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int
    LOGIN_RATE_LIMIT_WINDOW_SECONDS: int

    REGISTER_RATE_LIMIT_MAX_ATTEMPTS: int
    REGISTER_RATE_LIMIT_WINDOW_SECONDS: int

    GOOGLE_LOGIN_RATE_LIMIT_MAX_ATTEMPTS: int = 30
    GOOGLE_LOGIN_RATE_LIMIT_WINDOW_SECONDS: int = 60
    GOOGLE_VERIFICATION_MAX_CONCURRENCY: int = 8

    ORIGINS_API: list[str]
    TRUSTED_PROXY_IPS: list[str] = []
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
