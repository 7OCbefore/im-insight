"""
Configuration Management Module for IM-Insight.
Handles loading and validation of application settings from YAML file with environment variable overrides.
"""

import os
from pathlib import Path
from typing import List
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


class AppConfig(BaseModel):
    """Application-level configuration."""
    name: str
    debug: bool
    environment: str


class IngestionConfig(BaseModel):
    """Message ingestion configuration."""
    scan_interval_min: float
    scan_interval_max: float
    target_window_title: str
    monitor_groups: List[str] = ["all"]


class IntelligenceConfig(BaseModel):
    """LLM intelligence processing configuration."""
    enabled: bool
    provider: str
    endpoint_url: str
    api_key: SecretStr
    model: str
    temperature: float
    timeout: int


class RulesConfig(BaseModel):
    """Content filtering rules configuration."""
    whitelist: List[str]
    blacklist: List[str]


class Settings(BaseSettings):
    """Root settings model with environment variable override support."""
    model_config = SettingsConfigDict(
        env_prefix="IM_INSIGHT_",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    app: AppConfig
    ingestion: IngestionConfig
    intelligence: IntelligenceConfig
    rules: RulesConfig


def load_settings(config_path: str = "config/settings.yaml") -> Settings:
    """
    Load and validate settings from YAML file with environment variable overrides.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Validated Settings object
        
    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the configuration file is invalid YAML
        ValidationError: If the configuration doesn't match the schema
    """
    # Check if config file exists
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please create it with the required settings structure."
        )
    
    # Load YAML config
    with open(config_file, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)
    
    # Create settings object (will automatically handle env var overrides)
    return Settings(**config_data)


# Singleton instance
_settings: Settings = None


def get_settings() -> Settings:
    """
    Get singleton instance of validated settings.
    
    Returns:
        Validated Settings object
    """
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings