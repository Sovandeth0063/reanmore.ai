from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_FAST_MODEL: str = "gemini-2.0-flash"
    GEMINI_REASONING_MODEL: str = "gemini-2.0-flash-thinking"
    GEMINI_VISION_MODEL: str = "gemini-2.0-flash"
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

    # Phase 0 Runtime & Concurrency Control (Spec Section 5.3, 12.2)
    LLM_MAX_INFLIGHT: int = 1
    LLM_FIRST_TOKEN_TIMEOUT_SEC: float = 6.0
    LLM_TOTAL_TURN_TIMEOUT_SEC: float = 15.0
    LLM_NUM_PREDICT: int = 220

    MATH_SERVICE_PORT: int = 9001
    SCIENCE_SERVICE_PORT: int = 9002
    HOMEWORK_SCANNER_PORT: int = 9003
    
    MATH_SERVICE_URL: str = "http://math-service:9001"
    SCIENCE_SERVICE_URL: str = "http://science-service:9002"
    HOMEWORK_SCANNER_URL: str = ""
    
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/science_chatbot"

    # MinIO File Vault Storage (Spec Section 8, Section 11)
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_DOCUMENTS: str = "documents"
    MINIO_BUCKET_SCANS: str = "student-scans"
    MINIO_SECURE: bool = False

    # Authentication & Session Security
    AUTH_SECRET_KEY: str = "reanmore_insecure_default_secret_key_change_in_prod"
    AUTH_TOKEN_EXPIRE_DAYS: int = 30

    # Problem Quota System (10 problems/day, 300 problems/month, Asia/Phnom_Penh reset)
    QUOTA_DAILY: int = 10
    QUOTA_MONTHLY: int = 300
    QUOTA_TZ: str = "Asia/Phnom_Penh"

    # Safeguarding Escalation Dispatch (Spec Section 9, Phase 5)
    SAFEGUARDING_WEBHOOK_URL: str = ""
    SAFEGUARDING_ALERT_EMAIL: str = ""
    SAFEGUARDING_DISPATCH_TIMEOUT_SEC: float = 3.0

    # Feature Flags & Deferrals (Spec Section 1 & Section 16 Decision)
    # Shipped in MVP: Khmer UI toggle + dynamic /api/translate (LLM, with English fallback).
    # Deferred to v2.2: Khmer segmentation, parallel prompts, MoEYS ingestion, word-problem parser.
    ENABLE_KHMER_LANGUAGE: bool = True
    ENABLE_VOICE_STT: bool = False
    # Worksheet photo OCR is deferred to Phase 4 (Architecture v2.1 Section 16).
    # The /api/upload endpoints return 404 unless this is explicitly enabled.
    ENABLE_API_OCR: bool = False

    # Microservice monitoring & circuit breaker configuration 
    HEALTH_CHECK_INTERVAL_SEC: int = 60
    HEALTH_CHECK_TIMEOUT_SEC: int = 5
    CIRCUIT_FAILURE_THRESHOLD: int = 3
    CIRCUIT_RECOVERY_TIMEOUT_SEC: float = 30.0
    DEGRADED_LATENCY_THRESHOLD_MS: float = 1000.0

settings = Settings()

