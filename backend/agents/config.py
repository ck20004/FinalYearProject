from pydantic_settings import BaseSettings
from typing import Optional

class AgentConfig(BaseSettings):
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.2:3b"
    fallback_model: str = "qwen3:4b"

    # Agent Settings
    max_retries: int = 3
    timeout_seconds: int = 300
    temperature: float = 0.3
    # max_tokens: int = 2000

    # Ollama generation parameters
    # num_ctx: int = 2048  # Reduced context window
    top_p: float = 0.8  # More focused sampling
    repeat_penalty: float = 1.05  # Reduce repetition

    # Available Models (you can modify this list)
    available_models: list = [
        # "granite3.1-moe:3b",
        # "cogito:3b", 
        # "phi3:3.8b",
        # "phi4-mini-reasoning:3.8b",
        # "qwen2.5vl:3b",
        # "qwen3:4b",
        # "gemma3:4b",
        "llama3.2:3b"
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"

agent_config = AgentConfig()