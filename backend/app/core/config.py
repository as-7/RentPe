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

    APP_TIMEZONE: str = "Asia/Kolkata"

    WHATSAPP_ENABLED: bool = False
    WHATSAPP_GRAPH_VERSION: str = "v23.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_TEMPLATE_NAME: str = ""
    WHATSAPP_TEMPLATE_LANGUAGE: str = "en"
    WHATSAPP_DEFAULT_COUNTRY_CODE: str = "91"
    WHATSAPP_REMINDER_OFFSETS: str = "3,1,0"
    WHATSAPP_REMINDER_HOUR: int = 9
    WHATSAPP_REMINDER_MINUTE: int = 0
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
