from pydantic_settings import BaseSettings
from typing import Optional

class AWSConfig(BaseSettings):
    """
    AWS Configuration settings.
    Credentials can be provided via environment variables,
    which is the standard for boto3.
    (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN)
    """
    aws_region: str = "ap-south-1"
    
    # Optional: For development, you can set these directly, but it's not recommended.
    # Boto3 will automatically pick them up from the environment.
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

aws_config = AWSConfig()