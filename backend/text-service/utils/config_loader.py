"""
Configuration loader for SkillScreen
Handles loading sensitive configuration data from .config file
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

class ConfigLoader:
    """Loads configuration from .config file"""
    
    def __init__(self, config_file: str = ".config"):
        # Look for config file in the same directory as this module
        module_dir = Path(__file__).parent.parent
        self.config_file = module_dir / config_file
        self.config_data = {}
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from file"""
        config_path = Path(self.config_file) if isinstance(self.config_file, str) else self.config_file
        
        if not config_path.exists():
            print(f"Warning: Configuration file {self.config_file} not found. Using environment variables.")
            return
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    # Parse key=value pairs
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        
                        self.config_data[key] = value
                        
        except Exception as e:
            print(f"Error loading configuration file: {e}")
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get configuration value"""
        # First check environment variables (highest priority)
        env_value = os.environ.get(key)
        if env_value:
            return env_value
        
        # Then check config file
        config_value = self.config_data.get(key)
        if config_value:
            return config_value
        
        # Finally return default
        return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean configuration value"""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer configuration value"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values"""
        return self.config_data.copy()

# Global configuration instance
config = ConfigLoader()

# Convenience functions
def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get configuration value"""
    return config.get(key, default)

def get_bool_config(key: str, default: bool = False) -> bool:
    """Get boolean configuration value"""
    return config.get_bool(key, default)

def get_int_config(key: str, default: int = 0) -> int:
    """Get integer configuration value"""
    return config.get_int(key, default)
