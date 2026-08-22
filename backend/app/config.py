"""CropGuard Network — Application configuration.

Reads from .env file via pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cropguard"
    db_user: str = "postgres"
    db_password: str = "cropguard_dev"

    # MongoDB
    mongo_uri: str = "mongodb://localhost:27017/cropguard"

    # Kafka
    kafka_broker: str = "localhost:9092"

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5000"

    # YOLOv8
    yolo_model_dir: str = "./vision_training/runs"

    # Azure (blank for local dev)
    azure_storage_connection_string: str = ""
    azure_blob_container: str = "crop-images"

    # Groq LLM
    llm_api_key: str = ""
    llm_model: str = "llama-3.3-70b-versatile"
    llm_model_light: str = "llama-3.1-8b-instant"

    # ChromaDB
    vector_db_url: str = "http://localhost:8000"

    # JWT
    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    # Vision / Diagnosis
    confidence_threshold: float = 0.60
    max_upload_size_mb: int = 10
    blur_threshold: float = 100.0
    brightness_min: int = 40
    brightness_max: int = 220

    @property
    def database_url(self) -> str:
        """Async database URL for the application (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Sync database URL for Alembic migrations (psycopg2 driver)."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


settings = Settings()
