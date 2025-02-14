from typing import Dict, Any, Optional
import os
import yaml
import json
from pathlib import Path


class Config:
    def __init__(self, env: str = "development"):
        self.env = env
        self.config_path = Path(__file__).parent.parent / "config"
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        config_file = self.config_path / f"{self.env}.yaml"

        if not config_file.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {config_file}"
            )

        with open(config_file) as f:
            config = yaml.safe_load(f)

        # Override with environment variables
        self._override_from_env(config)

        # Validate configuration
        self._validate_config(config)

        return config

    def _override_from_env(self, config: Dict[str, Any]):
        """Override configuration with environment variables"""
        for key in config:
            env_key = f"CYNIX_{key.upper()}"
            env_value = os.getenv(env_key)

            if env_value:
                try:
                    # Try to parse as JSON
                    config[key] = json.loads(env_value)
                except json.JSONDecodeError:
                    # Use as string if not valid JSON
                    config[key] = env_value

    def _validate_config(self, config: Dict[str, Any]):
        """Validate required configuration values"""
        required_keys = {
            "solana_rpc_url": str,
            "redis_url": str,
            "github_token": str,
            "twitter_bearer_token": str,
            "telegram_bot_token": str,
            "cynix_token_address": str
        }

        for key, expected_type in required_keys.items():
            if key not in config:
                raise ValueError(f"Missing required config key: {key}")
            if not isinstance(config[key], expected_type):
                raise TypeError(
                    f"Invalid type for {key}. Expected {expected_type.__name__}"
                )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config_data.get(key, default)

    def get_nested(
            self,
            path: str,
            default: Any = None
    ) -> Any:
        """Get nested configuration value using dot notation"""
        keys = path.split(".")
        value = self.config_data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default

            if value is None:
                return default

        return value

    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.env == "production"

    @property
    def debug(self) -> bool:
        """Get debug mode status"""
        return self.get("debug", False)