"""Configuration management for Research Agent"""

import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import BaseModel, Field, ConfigDict
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent


class OllamaConfig(BaseModel):
    """Ollama configuration"""
    model_config = ConfigDict(extra="ignore")
    base_url: str = Field(default="http://host.docker.internal:11434")
    model: str = Field(default="qwen3:30b")
    timeout: int = Field(default=120)
    max_retries: int = Field(default=3)
    context_length: int = Field(default=8192)
    temperature: float = Field(default=0.7)
    top_p: float = Field(default=0.9)


class MCPConfig(BaseModel):
    """MCP Server configuration"""
    model_config = ConfigDict(extra="ignore")
    searxng_url: str = Field(default="http://host.docker.internal:8090")
    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)


class ContentFetchingConfig(BaseModel):
    """Content fetching configuration"""
    model_config = ConfigDict(extra="ignore")
    max_concurrent: int = Field(default=5)
    timeout: int = Field(default=10)
    max_content_size: int = Field(default=1048576)  # 1MB
    user_agent: str = Field(default="Mozilla/5.0 (Research-Agent/1.0)")
    max_retries: int = Field(default=3)
    backoff_factor: float = Field(default=2.0)


class ResearchConfig(BaseModel):
    """Research configuration"""
    model_config = ConfigDict(extra="ignore")
    default_depth: str = Field(default="standard")
    max_sources: int = Field(default=20)
    min_sources: int = Field(default=5)
    quality_threshold: float = Field(default=0.7)
    max_research_time: int = Field(default=300)
    chunk_size: int = Field(default=4000)


class RedisConfig(BaseModel):
    """Redis configuration"""
    model_config = ConfigDict(extra="ignore")
    host: str = Field(default="localhost")
    port: int = Field(default=6379)
    db: int = Field(default=0)
    password: Optional[str] = Field(default=None)
    decode_responses: bool = Field(default=True)


class CacheConfig(BaseModel):
    """Cache configuration"""
    model_config = ConfigDict(extra="ignore")
    enabled: bool = Field(default=True)
    search_ttl: int = Field(default=3600)  # 1 hour
    content_ttl: int = Field(default=86400)  # 24 hours
    report_ttl: int = Field(default=604800)  # 7 days


class DatabaseConfig(BaseModel):
    """Database configuration"""
    model_config = ConfigDict(extra="ignore")
    url: str = Field(default="postgresql://research_user:research_pass_2024@postgres:5432/research_agent")
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=40)
    echo: bool = Field(default=False)


class AuthConfig(BaseModel):
    """Authentication configuration"""
    model_config = ConfigDict(extra="ignore")
    secret_key: str = Field(default="your-secret-key-change-this-in-production-" + os.urandom(16).hex())
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)


class ServerConfig(BaseModel):
    """API server configuration"""
    model_config = ConfigDict(extra="ignore")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    workers: int = Field(default=4)
    reload: bool = Field(default=False)


class Settings(BaseSettings):
    """Application settings"""

    model_config = ConfigDict(
        extra="ignore",  # Ignore extra fields
        env_prefix="",
        env_nested_delimiter="__"
    )

    # Application
    app_name: str = Field(default="Research Agent")
    app_version: str = Field(default="1.0.0")
    debug: bool = Field(default=False)
    environment: str = Field(default="development")

    # Component configs
    server: ServerConfig = Field(default_factory=ServerConfig)
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    content_fetching: ContentFetchingConfig = Field(default_factory=ContentFetchingConfig)
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> "Settings":
        """Load settings from YAML file and environment variables"""
        if config_path is None:
            config_path = PROJECT_ROOT / "config" / "default.yaml"

        settings_dict = {}

        # Load from YAML if exists
        if config_path.exists():
            with open(config_path, "r") as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    settings_dict = cls._flatten_config(yaml_config)

        # Override with environment variables
        settings = cls(**settings_dict)

        # Apply environment variable overrides
        settings.ollama.base_url = os.getenv("OLLAMA_BASE_URL", settings.ollama.base_url)
        settings.ollama.model = os.getenv("OLLAMA_MODEL", settings.ollama.model)
        settings.mcp.searxng_url = os.getenv("MCP_SEARXNG_URL", settings.mcp.searxng_url)
        settings.redis.host = os.getenv("REDIS_HOST", settings.redis.host)
        settings.redis.port = int(os.getenv("REDIS_PORT", str(settings.redis.port)))
        settings.server.host = os.getenv("API_HOST", settings.server.host)
        settings.server.port = int(os.getenv("API_PORT", str(settings.server.port)))
        settings.log_level = os.getenv("LOG_LEVEL", settings.log_level)
        settings.database.url = os.getenv("DATABASE_URL", settings.database.url)
        settings.auth.secret_key = os.getenv("AUTH_SECRET_KEY", settings.auth.secret_key)

        return settings

    @staticmethod
    def _flatten_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Flatten nested configuration for Pydantic models"""
        return config


# Global settings instance
settings = Settings.load_from_yaml()