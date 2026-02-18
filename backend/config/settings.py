from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Server settings
    port: int = 8000
    host: str = "0.0.0.0"
    environment: str = "development"
    
    # GitHub settings
    github_token: Optional[str] = None
    
    # Session settings
    session_timeout: int = 3600  # 1 hour
    
    # API settings
    max_file_size: int = 50  # Maximum files to fetch from GitHub
    
    class Config:
        env_file = ".env"

settings = Settings()