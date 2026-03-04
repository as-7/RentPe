from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "RentPe Backend"
    API_V1_STR: str = "/api/v1"
    
    # Supabase / PostgreSQL Connection String
    # Format: postgresql+asyncpg://user:password@host:port/db
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/rentpe"
    
    # JWT / Auth Configuration
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days
    
    class Config:
        env_file = ".env"

settings = Settings()
