"""
TUBECRAFT Configuration
Application settings and configuration management
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # App Info
    app_name: str = "TUBECRAFT Generator"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Database
    postgres_user: str = "tubecraft"
    postgres_password: str = "tubecraft2024"
    postgres_db: str = "tubecraft_db"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    
    # Ollama
    ollama_host: str = "http://ollama:11434"
    ollama_model: str = "mistral:7b"
    ollama_timeout: int = 300
    
    # TTS Settings
    tts_model: str = "ja_JP-takumi-medium"
    tts_voice_speed: float = 1.0
    tts_max_chunk_size: int = 1000
    tts_sample_rate: int = 22050
    
    # Video Settings
    video_fps: int = 30
    video_resolution: str = "1920x1080"
    video_quality: str = "high"
    video_codec: str = "libx264"
    
    # Audio Settings
    audio_sample_rate: int = 44100
    audio_bitrate: str = "192k"
    audio_format: str = "mp3"
    
    # File Paths
    data_path: str = "/data"
    models_path: str = "/models"
    
    @property
    def audio_output_path(self) -> str:
        return os.path.join(self.data_path, "audio")
    
    @property
    def video_output_path(self) -> str:
        return os.path.join(self.data_path, "video")
    
    @property
    def metadata_path(self) -> str:
        return os.path.join(self.data_path, "metadata")
    
    # Performance
    max_concurrent_jobs: int = 3
    worker_threads: int = 4
    memory_limit_gb: int = 8
    cpu_limit: int = 4
    
    # API Security
    api_secret_key: str = "your-secret-key-here-change-in-production"
    api_algorithm: str = "HS256"
    api_access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["*"]
    
    # Logging
    log_level: str = "info"
    log_format: str = "json"
    
    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # Optional GPU
    enable_gpu: bool = False
    cuda_visible_devices: str = "0"
    
    # Phase 2 Features (disabled by default)
    enable_youtube_api: bool = False
    youtube_api_key: Optional[str] = None
    youtube_client_id: Optional[str] = None
    youtube_client_secret: Optional[str] = None
    
    enable_s3_storage: bool = False
    s3_endpoint: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_bucket_name: Optional[str] = None
    s3_region: str = "us-east-1"
    
    # Webhook URLs
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable prefix
        env_prefix = ""
        
        # Allow extra fields for future extensions
        extra = "ignore"


# Create global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings