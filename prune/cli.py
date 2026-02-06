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


# Required by arguably for --version flag
__version__ = _pkg_version
__all__ = ['verify', 'check_deps', 'main']


@arguably.command
def verify(
    requirements_file: Path,
    *source_paths: Path,
    config: Path | None = None
):
    """
    Verify requirements.txt against actual imports in Python files.
    
    Args:
        requirements_file: Path to requirements.txt file
        *source_paths: One or more source paths to scan for Python files
        config: Path to existing extras configuration file (JSON)
    
    Examples:
        prune verify requirements.txt ./app
        prune verify requirements.txt ./app ./tests
        prune verify requirements.txt ./app --config extras_config.json
    """
    if not source_paths:
        print("❌ Error: At least one source path is required", file=sys.stderr)
        sys.exit(1)
    
    verify_requirements(requirements_file, list(source_paths), config)


@arguably.command(alias="check-deps")
def check_deps(
    requirements_file: Path,
    *,
    output: Path | None = None
):
    """
    Check dependencies by fetching metadata from PyPI.
    
    Args:
        requirements_file: Path to requirements.txt file
        output: Output path for configuration file (if not provided, prints to terminal)
    
    Examples:
        prune check-deps requirements.txt
        prune check-deps requirements.txt --output extras_config.json
    """
    print(f"📋 Reading requirements from: {requirements_file}")
    requirements = parse_requirements(requirements_file)
    print(f"   Found {len(requirements)} packages")
    
    create_config_from_requirements(requirements_file, requirements, output)


def main():
    """Entry point for the CLI."""
    import sys
    # Set __version__ in the calling module for arguably to find
    sys.modules['__main__'].__version__ = __version__
    arguably.run(name="prune", always_subcommand=True, version_flag=True)


if __name__ == '__main__':
    main()
