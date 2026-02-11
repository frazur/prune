"""Configuration management for prune."""

import json
import sys
from pathlib import Path
from typing import Dict, Optional

from .constants import PACKAGE_MAPPINGS, DEFAULT_RUNTIME_DEPENDENCIES, PRUNE_DIR, PRUNE_CONFIG_FILE


def merge_runtime_dependencies(base: Dict[str, list], additional: Dict[str, list]) -> None:
    """
    Merge runtime dependencies, combining lists for same packages.
    
    Args:
        base: Base dictionary to merge into (modified in-place)
        additional: Additional dependencies to merge in
    """
    for pkg, deps in additional.items():
        if pkg in base:
            # Merge: add additional deps to base (avoid duplicates)
            base[pkg] = list(set(base[pkg] + deps))
        else:
            base[pkg] = list(deps)


def load_config(config_file: Optional[Path] = None) -> Dict:
    """
    Load configuration from file or use defaults.
    
    Priority (high to low):
    1. User overrides (_user_overrides section in config)
    2. PyPI-discovered config (from .prune/prune-conf.json)
    3. Hardcoded defaults (from constants.py)
    
    Args:
        config_file: Optional path to configuration file
        
    Returns:
        Configuration dictionary with merged settings
    """
    # If no explicit config provided, check for .prune/prune-conf.json
    if not config_file:
        default_config_path = Path.cwd() / PRUNE_DIR / PRUNE_CONFIG_FILE
        if default_config_path.exists():
            config_file = default_config_path
    
    if config_file and config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"📝 Loaded configuration from: {config_file}")
                
                # Start with hardcoded defaults
                merged_mappings = dict(PACKAGE_MAPPINGS)
                merged_runtime_deps = {pkg: list(deps) for pkg, deps in DEFAULT_RUNTIME_DEPENDENCIES.items()}
                
                # Merge PyPI-discovered config
                config_mappings = config.get('package_mappings', {})
                config_runtime_deps = config.get('runtime_dependencies', {})
                
                merged_mappings.update(config_mappings)
                merge_runtime_dependencies(merged_runtime_deps, config_runtime_deps)
                
                # Merge user overrides (highest priority)
                user_overrides = config.get('_user_overrides', {})
                if user_overrides:
                    override_mappings = user_overrides.get('package_mappings', {})
                    override_runtime = user_overrides.get('runtime_dependencies', {})
                    
                    merged_mappings.update(override_mappings)
                    merge_runtime_dependencies(merged_runtime_deps, override_runtime)
                
                # Update config with merged values
                config['package_mappings'] = merged_mappings
                config['runtime_dependencies'] = merged_runtime_deps
                
                return config
        except Exception as e:
            print(f"⚠️  Error loading config file: {e}, using defaults", file=sys.stderr)
    
    return {
        "package_mappings": PACKAGE_MAPPINGS,
        "runtime_dependencies": DEFAULT_RUNTIME_DEPENDENCIES,
        "package_extras": {}
    }
