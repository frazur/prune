"""
CLI entry point for prune.

Defines the command-line interface using arguably.
"""

import sys
import arguably
from pathlib import Path

from . import __version__ as _pkg_version
from .core import verify_requirements
from .parser import parse_requirements
from .pypi import create_config_from_requirements
from .constants import PRUNE_DIR, PRUNE_CONFIG_FILE, DEFAULT_EXTRAS_CONFIG
import json


# Required by arguably for --version flag
__version__ = _pkg_version
__all__ = ['verify', 'init', 'main']


@arguably.command
def verify(
    *source_paths: Path,
    requirements_file: Path = Path("requirements.txt"),
    config: Path | None = None,
    mapping: bool = False
):
    """
    Verify requirements.txt against actual imports in Python files.
    
    Args:
        source_paths: One or more source paths to scan for Python files
        requirements_file: Path to requirements file (default: requirements.txt)
        config: Path to existing extras configuration file (JSON)
        mapping: Generate detailed .mapping and .unmatched-mapping files
    
    Examples:
        prune verify ./app
        prune verify ./app ./tests
        prune verify ./app --requirements-file custom-reqs.txt
        prune verify ./app --config extras_config.json
        prune verify ./app --mapping
    """
    if not source_paths:
        print("❌ Error: At least one source path is required", file=sys.stderr)
        sys.exit(1)
    
    verify_requirements(requirements_file, list(source_paths), config, generate_mapping=mapping)


@arguably.command
def init(
    *,
    req: Path | None = None,
    update: bool = False
):
    """
    Initialize the .prune directory and configuration.
    
    Args:
        req: Path to requirements file to generate config from (default: requirements.txt)
        update: Update existing configuration from requirements file
    
    Examples:
        prune init                           # Create config from requirements.txt if exists
        prune init --req custom-reqs.txt     # Create config from specific file
        prune init --update                  # Update config from requirements.txt
        prune init --update --req dev.txt    # Update config from specific file
    """
    # Create .prune directory if it doesn't exist
    prune_dir = Path.cwd() / PRUNE_DIR
    prune_dir.mkdir(exist_ok=True)
    print(f"📁 Initialized directory: {prune_dir}")
    
    config_path = prune_dir / PRUNE_CONFIG_FILE
    
    # Determine requirements file to use
    requirements_file = req if req else Path("requirements.txt")
    
    # Check if we're updating or creating new
    if update:
        if not config_path.exists():
            print(f"⚠️  No existing configuration found at {config_path}")
            print("   Creating new configuration...")
        else:
            print(f"🔄 Updating configuration: {config_path}")
    
    # Try to generate config from requirements file
    if requirements_file.exists():
        print(f"📋 Reading requirements from: {requirements_file}")
        requirements = parse_requirements(requirements_file)
        print(f"   Found {len(requirements)} packages")
        create_config_from_requirements(requirements_file, requirements, config_path)
    else:
        # Create default config if no requirements file
        if req:
            # User specified a file that doesn't exist
            print(f"❌ Error: Requirements file not found: {requirements_file}", file=sys.stderr)
            sys.exit(1)
        else:
            # No requirements.txt found, create default
            print("⚠️  No requirements.txt found, creating default configuration")
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_EXTRAS_CONFIG, f, indent=2)
                print(f"✅ Created default configuration: {config_path}")
            except Exception as e:
                print(f"❌ Error creating config file: {e}", file=sys.stderr)
                sys.exit(1)


def main():
    """Entry point for the CLI."""
    import sys
    # Set __version__ in the calling module for arguably to find
    sys.modules['__main__'].__version__ = __version__
    arguably.run(name="prune", always_subcommand=True, version_flag=True)


if __name__ == '__main__':
    main()
