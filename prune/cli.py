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
from . import overrides
import json


# Required by arguably for --version flag
__version__ = _pkg_version
__all__ = ['verify', 'init', 'override', 'main']


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


@arguably.command(alias="override__ls")
def override__list():
    """
    List all user overrides.
    
    Shows package mappings and runtime dependencies that have been
    manually configured for this project.
    
    Examples:
        prune override list
        prune override ls
    """
    overrides.list_overrides()


@arguably.command
def override__ls():
    """Alias for override list."""
    overrides.list_overrides()


@arguably.command
def override__add_mapping(import_name: str, package_name: str):
    """
    Add a package mapping override.
    
    Maps an import name to a package name. Useful for custom packages
    or when the import name doesn't match the package name.
    
    Args:
        import_name: The import name (e.g., 'mylib')
        package_name: The package name in requirements.txt (e.g., 'my-custom-package')
    
    Examples:
        prune override add-mapping mylib my-custom-package
        prune override add-mapping internal company-internal-lib
    """
    overrides.add_mapping(import_name, package_name)


@arguably.command(alias="override__rm_mapping")
def override__remove_mapping(import_name: str):
    """
    Remove a package mapping override.
    
    Args:
        import_name: The import name to remove
    
    Examples:
        prune override remove-mapping mylib
        prune override rm-mapping mylib
    """
    overrides.remove_mapping(import_name)


@arguably.command
def override__rm_mapping(import_name: str):
    """Alias for override remove-mapping."""
    overrides.remove_mapping(import_name)


@arguably.command
def override__add_runtime(trigger_package: str, dependency: str):
    """
    Add a runtime dependency override.
    
    Specifies that when trigger_package is used, dependency should also
    be marked as used even if not directly imported.
    
    Args:
        trigger_package: The package that triggers the dependency
        dependency: The runtime dependency to add
    
    Examples:
        prune override add-runtime fastapi custom-auth-middleware
        prune override add-runtime my-framework required-plugin
    """
    overrides.add_runtime(trigger_package, dependency)


@arguably.command
def override__remove_runtime(trigger_package: str, dependency: str):
    """
    Remove a runtime dependency override.
    
    Args:
        trigger_package: The package that triggers the dependency
        dependency: The runtime dependency to remove
    
    Examples:
        prune override remove-runtime fastapi custom-auth-middleware
    """
    overrides.remove_runtime(trigger_package, dependency)


@arguably.command
def override__clear():
    """
    Clear all user overrides.
    
    Removes all custom package mappings and runtime dependencies.
    This action requires confirmation.
    
    Examples:
        prune override clear
    """
    overrides.clear_overrides()


def main():
    """Entry point for the CLI."""
    import sys
    # Set __version__ in the calling module for arguably to find
    sys.modules['__main__'].__version__ = __version__
    arguably.run(name="prune", always_subcommand=True, version_flag=True)


if __name__ == '__main__':
    main()
