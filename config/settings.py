"""
Configuration management for CPG Compliance AI Agents
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
  
    # Environment
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
  
    # Application
    APP_NAME: str = "CPG Compliance AI Agents"
    VERSION: str = "1.0.0"
    RUN_MODE: str = Field(default="single", env="RUN_MODE")
  
    # Monitoring
    MONITORING_INTERVAL: int = Field(default=3600, env="MONITORING_INTERVAL")
    COMPLIANCE_THRESHOLD: float = Field(default=85.0, env="COMPLIANCE_THRESHOLD")
  
    # Directories
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
  
    # Azure Services
    AZURE_STORAGE_CONNECTION_STRING: str = Field(default="mock://localhost", env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_SERVICE_BUS_CONNECTION_STRING: str = Field(default="mock://localhost", env="AZURE_SERVICE_BUS_CONNECTION_STRING")
    AZURE_COGNITIVE_SERVICES_KEY: str = Field(default="mock-key", env="AZURE_COGNITIVE_SERVICES_KEY")
    AZURE_COGNITIVE_SERVICES_ENDPOINT: str = Field(default="mock://localhost", env="AZURE_COGNITIVE_SERVICES_ENDPOINT")
  
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./data/compliance.db", env="DATABASE_URL")
  
    # API
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
  
    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
    # Agent Configuration
    MAX_CONCURRENT_AGENTS: int = Field(default=5, env="MAX_CONCURRENT_AGENTS")
    AGENT_TIMEOUT: int = Field(default=300, env="AGENT_TIMEOUT")
  
    # Memory Configuration
    MEMORY_RETENTION_DAYS: int = Field(default=30, env="MEMORY_RETENTION_DAYS")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
  
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    OPENAI_MODEL: str = Field(default="gpt-4", env="OPENAI_MODEL")

    @property
    def is_mock_mode(self) -> bool:
        return self.ENVIRONMENT == "mock"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # This allows extra fields to be ignored
  
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ensure_directories()
  
    def ensure_directories(self):
        """Ensure required directories exist."""
        directories = [
            self.DATA_DIR,
            self.DATA_DIR / "contracts",
            self.DATA_DIR / "planograms", 
            self.DATA_DIR / "images",
            self.DATA_DIR / "reports",
            self.DATA_DIR / "cache",
            self.LOGS_DIR
        ]
      
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)