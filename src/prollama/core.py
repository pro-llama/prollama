"""
Core functionality for Prollama
"""

from pathlib import Path
from typing import Any

import yaml
from rich.console import Console

console = Console()


class ProllamaCore:
    """Main core class for Prollama functionality"""

    def __init__(self, config_path: str | None = None):
        self.config_path = config_path or "prollama.yaml"
        self.config: dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from YAML file"""
        config_file = Path(self.config_path)
        if config_file.exists():
            try:
                with open(config_file) as f:
                    self.config = yaml.safe_load(f) or {}
                console.print(f"[green]✓[/green] Loaded config from {self.config_path}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load config: {e}")
                self.config = {}
        else:
            console.print(f"[yellow]⚠[/yellow] Config file {self.config_path} not found, using defaults")
            self.config = self.get_default_config()

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration"""
        return {
            "llm": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "api_key": "${OPENAI_API_KEY}"
            },
            "proxy": {
                "enabled": False,
                "host": "localhost",
                "port": 8080
            },
            "tickets": {
                "provider": "github",
                "repo": "owner/repo"
            }
        }

    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            console.print(f"[green]✓[/green] Saved config to {self.config_path}")
        except Exception as e:
            console.print(f"[red]✗[/red] Failed to save config: {e}")

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value by key (supports dot notation)"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
