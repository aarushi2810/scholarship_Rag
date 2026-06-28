from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    

    QDRANT_URL: str
    QDRANT_API_KEY: str
    QDRANT_COLLECTION: str = "scholarships"
    REDIS_URL: str = "redis://localhost:6379"
    POSTGRES_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/scholarshiprag"
    GEMINI_API_KEY: str = ""
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIM: int = 384

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
