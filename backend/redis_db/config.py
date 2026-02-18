from pydantic_settings import BaseSettings
from typing import Optional


class RedisConfig(BaseSettings):
    # Redis connection settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_url: Optional[str] = None
    
    # Connection pool settings
    redis_max_connections: int = 10
    redis_retry_on_timeout: bool = True
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # Session settings
    session_timeout: int = 3600  # 1 hour
    
    # Cache settings
    cache_timeout: int = 1800  # 30 minutes
    
    class Config:
        env_file = ".env"
        extra = "ignore"
    
    def get_redis_url(self) -> str:
        """Get Redis connection URL"""
        if self.redis_url:
            return self.redis_url
        
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        else:
            return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

redis_config = RedisConfig()