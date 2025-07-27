"""
Logging configuration for the application
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from config.settings import Settings

def setup_logging():
    """Setup application logging configuration."""
    settings = Settings()
  
    # Create logs directory if it doesn't exist
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)
  
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
  
    # Clear existing handlers
    root_logger.handlers.clear()
  
    # Create formatter
    formatter = logging.Formatter(settings.LOG_FORMAT)
  
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
  
    # File handler for all logs
    file_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "application.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
  
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "errors.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
  
    # Agent-specific logger
    agent_logger = logging.getLogger("agents")
    agent_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "agents.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    agent_handler.setFormatter(formatter)
    agent_logger.addHandler(agent_handler)
  
    # Workflow logger
    workflow_logger = logging.getLogger("workflows")
    workflow_handler = logging.handlers.RotatingFileHandler(
        settings.LOGS_DIR / "workflows.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    workflow_handler.setFormatter(formatter)
    workflow_logger.addHandler(workflow_handler)
  
    logging.info("Logging configuration initialized")