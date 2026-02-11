"""User overrides management for prune configuration."""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .constants import PRUNE_DIR, PRUNE_CONFIG_FILE


def ensure_config_exists() -> Path:
    """
    Ensure .prune directory and config file exist.
    
    Returns:
        Path to config file
        
    Raises:
        SystemExit: If config doesn't exist and can't be created
    """
    prune_dir = Path.cwd() / PRUNE_DIR
    config_path = prune_dir / PRUNE_CONFIG_FILE
    
    if not config_path.exists():
        print("❌ No configuration found. Run 'prune init' first.", file=sys.stderr)
        sys.exit(1)
    
    return config_path


def load_config_file(config_path: Path) -> Dict:
    """Load configuration from file."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}", file=sys.stderr)
        sys.exit(1)


def save_config_file(config_path: Path, config: Dict) -> None:
    """Save configuration to file."""
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"❌ Error saving config: {e}", file=sys.stderr)
        sys.exit(1)


def list_overrides() -> None:
    """List all user overrides."""
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    overrides = config.get('_user_overrides', {})
    
    if not overrides:
        print("No user overrides configured.")
        return
    
    # Package mappings
    mappings = overrides.get('package_mappings', {})
    if mappings:
        print("\n📦 Package Mappings:")
        for import_name, package_name in sorted(mappings.items()):
            print(f"   {import_name} → {package_name}")
    
    # Runtime dependencies
    runtime = overrides.get('runtime_dependencies', {})
    if runtime:
        print("\n🔧 Runtime Dependencies:")
        for trigger_pkg, deps in sorted(runtime.items()):
            for dep in deps:
                print(f"   {trigger_pkg} → {dep}")
    
    if not mappings and not runtime:
        print("No user overrides configured.")


def add_mapping(import_name: str, package_name: str) -> None:
    """
    Add a package mapping override.
    
    Args:
        import_name: The import name (e.g., 'mylib')
        package_name: The package name (e.g., 'my-custom-package')
    """
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    # Ensure _user_overrides exists
    if '_user_overrides' not in config:
        config['_user_overrides'] = {}
    
    if 'package_mappings' not in config['_user_overrides']:
        config['_user_overrides']['package_mappings'] = {}
    
    # Add mapping
    config['_user_overrides']['package_mappings'][import_name] = package_name
    save_config_file(config_path, config)
    
    print(f"✅ Added mapping: {import_name} → {package_name}")


def remove_mapping(import_name: str) -> None:
    """
    Remove a package mapping override.
    
    Args:
        import_name: The import name to remove
    """
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    overrides = config.get('_user_overrides', {})
    mappings = overrides.get('package_mappings', {})
    
    if import_name not in mappings:
        print(f"⚠️  No mapping found for: {import_name}")
        return
    
    # Remove mapping
    del mappings[import_name]
    save_config_file(config_path, config)
    
    print(f"✅ Removed mapping: {import_name}")


def add_runtime(trigger_package: str, dependency: str) -> None:
    """
    Add a runtime dependency override.
    
    Args:
        trigger_package: The package that triggers the dependency
        dependency: The runtime dependency to add
    """
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    # Ensure _user_overrides exists
    if '_user_overrides' not in config:
        config['_user_overrides'] = {}
    
    if 'runtime_dependencies' not in config['_user_overrides']:
        config['_user_overrides']['runtime_dependencies'] = {}
    
    # Add runtime dependency
    if trigger_package not in config['_user_overrides']['runtime_dependencies']:
        config['_user_overrides']['runtime_dependencies'][trigger_package] = []
    
    if dependency not in config['_user_overrides']['runtime_dependencies'][trigger_package]:
        config['_user_overrides']['runtime_dependencies'][trigger_package].append(dependency)
        save_config_file(config_path, config)
        print(f"✅ Added runtime dependency: {trigger_package} → {dependency}")
    else:
        print(f"⚠️  Runtime dependency already exists: {trigger_package} → {dependency}")


def remove_runtime(trigger_package: str, dependency: str) -> None:
    """
    Remove a runtime dependency override.
    
    Args:
        trigger_package: The package that triggers the dependency
        dependency: The runtime dependency to remove
    """
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    overrides = config.get('_user_overrides', {})
    runtime = overrides.get('runtime_dependencies', {})
    
    if trigger_package not in runtime:
        print(f"⚠️  No runtime dependencies found for: {trigger_package}")
        return
    
    if dependency not in runtime[trigger_package]:
        print(f"⚠️  Dependency not found: {trigger_package} → {dependency}")
        return
    
    # Remove dependency
    runtime[trigger_package].remove(dependency)
    
    # Clean up empty lists
    if not runtime[trigger_package]:
        del runtime[trigger_package]
    
    save_config_file(config_path, config)
    print(f"✅ Removed runtime dependency: {trigger_package} → {dependency}")


def clear_overrides() -> None:
    """Clear all user overrides."""
    config_path = ensure_config_exists()
    config = load_config_file(config_path)
    
    overrides = config.get('_user_overrides', {})
    
    if not overrides:
        print("No user overrides to clear.")
        return
    
    # Confirm before clearing
    response = input("⚠️  This will remove all user overrides. Continue? [y/N]: ").strip().lower()
    if response not in ['y', 'yes']:
        print("Cancelled.")
        return
    
    # Clear overrides
    config['_user_overrides'] = {}
    save_config_file(config_path, config)
    
    print("✅ All user overrides cleared.")
