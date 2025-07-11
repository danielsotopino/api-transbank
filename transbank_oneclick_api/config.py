import os
from pydantic_settings import BaseSettings
from typing import List, Optional

# Determinar el nombre del archivo de entorno
project_name = os.getenv("PROJECT_NAME", "transbank-oneclick-api")
custom_env_file = f".env.{project_name}"

env_file = custom_env_file if os.path.exists(custom_env_file) else ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "Transbank Oneclick API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str
    DATABASE_ENCRYPT_KEY: str
    
    # Transbank Configuration
    TRANSBANK_ENVIRONMENT: str = "integration"
    TRANSBANK_COMMERCE_CODE: str = "597055555541"
    TRANSBANK_API_KEY: str = "579B532A7440BB0C9079DED94D31EA1615BACEB56610332264630D42D0A36B1C"
    
    # Security
    SECRET_KEY: str
    
    # Redis (optional)
    REDIS_URL: Optional[str] = None
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    SERVICE_NAME: str = "api-transbank"
    SERVICE_VERSION: str = "1.0.0"
    
    # Rate Limiting
    RATE_LIMIT_INSCRIPTION: int = 10
    RATE_LIMIT_TRANSACTION: int = 100
    RATE_LIMIT_QUERY: int = 1000
    
    class Config:
        env_file = env_file
        case_sensitive = True

settings = Settings()