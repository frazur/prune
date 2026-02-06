"""Configuration management for prune."""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

from .constants import PACKAGE_MAPPINGS, DEFAULT_RUNTIME_DEPENDENCIES


def load_config(config_file: Optional[Path] = None) -> Dict:
    """
    Load configuration from file or use defaults.
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configuration dictionary
    """
    if config_file and config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"📝 Loaded configuration from: {config_file}")
                return config
        except Exception as e:
            print(f"⚠️  Error loading config file: {e}, using defaults", file=sys.stderr)
    
    return {
        "package_mappings": PACKAGE_MAPPINGS,
        "runtime_dependencies": DEFAULT_RUNTIME_DEPENDENCIES,
        "package_extras": {}
    }
