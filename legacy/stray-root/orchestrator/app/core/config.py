from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    ORCHESTRATOR_PORT: int = 9000
    MATH_SERVICE_PORT: int = 9001
    PHYSICS_SERVICE_PORT: int = 9002
    CHEMISTRY_SERVICE_PORT: int = 9003
    BIOLOGY_SERVICE_PORT: int = 9004
    
    MATH_SERVICE_URL: str = "http://math-service:9001"
    PHYSICS_SERVICE_URL: str = "http://physics-service:9002"
    CHEMISTRY_SERVICE_URL: str = "http://chemistry-service:9003"
    BIOLOGY_SERVICE_URL: str = "http://biology-service:9004"
    
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/science_chatbot"

    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
