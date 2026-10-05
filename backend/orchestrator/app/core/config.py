from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash"
    OPENAI_API_KEY: str = ""
    LLM_PRIMARY_PROVIDER: str = "gemini"
    LLM_FALLBACK_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_API_KEY: str = ""
    OLLAMA_MODEL: str = "qwen3.5:4b"
    OLLAMA_FAST_MODEL: str = "qwen3.5:4b"
    OLLAMA_REASONING_MODEL: str = "gemma4:e4b"
    OLLAMA_TRANSLATION_MODEL: str = "qwen3.5:4b"
    GEMINI_TEMPERATURE: float = 0.7
    OPENAI_TEMPERATURE: float = 0.7
    OLLAMA_TEMPERATURE: float = 0.2
    ORCHESTRATOR_PORT: int = 9000

    MATH_SERVICE_PORT: int = 9001
    SCIENCE_SERVICE_PORT: int = 9002
    HOMEWORK_SCANNER_PORT: int = 9003
    
    MATH_SERVICE_URL: str = "http://math-service:9001"
    SCIENCE_SERVICE_URL: str = "http://science-service:9002"
    HOMEWORK_SCANNER_URL: str = "http://homework-scanner:9003"
    
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/science_chatbot"

    # Microservice monitoring & circuit breaker configuration 
    HEALTH_CHECK_INTERVAL_SEC: int = 60
    HEALTH_CHECK_TIMEOUT_SEC: int = 5
    CIRCUIT_FAILURE_THRESHOLD: int = 3
    CIRCUIT_RECOVERY_TIMEOUT_SEC: float = 30.0
    DEGRADED_LATENCY_THRESHOLD_MS: float = 1000.0

settings = Settings()
