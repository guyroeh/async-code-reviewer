from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration manager.
    Reads variables from the environment or the .env file and validates their types.
    """

    project_name: str = "Automatic Code Review Platform"

    # LLM Configuration
    llm_provider_url: str = "http://localhost:11434/api/generate"
    llm_model_name: str = "llama3.2"
    llm_timeout_seconds: int = 120

    # System Constraints
    max_concurrent_scans: int = 5
    result_ttl_hours: int = 24
    
    # 50 KB Limit (50 * 1024 bytes) to protect the LLM context window
    max_file_size_bytes: int = 51200

    # Pydantic configuration to load the .env file automatically
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Create a global instance of settings to be imported across the app
settings = Settings()