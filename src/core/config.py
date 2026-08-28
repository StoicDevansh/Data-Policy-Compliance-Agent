"""
Data Policy Agent - Configuration Management
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml
from dotenv import load_dotenv

load_dotenv()


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    type: str = Field(default="sqlite", description="Database type: postgresql, mysql, sqlite, mongodb")
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    name: str = Field(default="dap_database.db")
    user: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None


class LLMConfig(BaseModel):
    """LLM provider configuration"""
    provider: str = Field(default="openai", description="LLM provider: openai, anthropic, local")
    model: str = Field(default="gpt-4")
    api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    temperature: float = Field(default=0.1)
    max_tokens: int = Field(default=4096)


class MonitoringConfig(BaseModel):
    """Periodic monitoring configuration"""
    enabled: bool = Field(default=True)
    interval_seconds: int = Field(default=3600)
    retry_on_failure: bool = Field(default=True)
    max_retries: int = Field(default=3)


class DashboardConfig(BaseModel):
    """Dashboard configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080)
    debug: bool = Field(default=False)


class AlertConfig(BaseModel):
    """Alert notification configuration"""
    email_enabled: bool = Field(default=False)
    smtp_host: Optional[str] = None
    smtp_port: int = Field(default=587)
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    recipients: List[str] = Field(default_factory=list)
    
    slack_enabled: bool = Field(default=False)
    slack_webhook_url: Optional[str] = None


class Settings(BaseSettings):
    """Main application settings"""
    app_name: str = "Data Policy Agent"
    version: str = "1.0.0"
    debug: bool = Field(default=False)
    
    # Base paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    policies_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "policies")
    
    # Sub-configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    alerts: AlertConfig = Field(default_factory=AlertConfig)
    
    # Internal database for storing rules and violations
    internal_db_path: Optional[str] = None
    
    class Config:
        env_prefix = "DAP_"
        env_nested_delimiter = "__"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default internal db path if not provided
        if self.internal_db_path is None:
            self.internal_db_path = str(self.data_dir / "dap_internal.db")
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.policies_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Settings":
        """Load settings from YAML file"""
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance"""
    global _settings
    if _settings is None:
        config_path = os.getenv("DAP_CONFIG_PATH", "config.yaml")
        if os.path.exists(config_path):
            _settings = Settings.from_yaml(config_path)
        else:
            _settings = Settings()
    return _settings


def update_settings(new_settings: Dict[str, Any]) -> Settings:
    """Update settings with new values"""
    global _settings
    current = get_settings().model_dump()
    current.update(new_settings)
    _settings = Settings(**current)
    return _settings
