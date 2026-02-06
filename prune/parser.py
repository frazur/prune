"""Parser for requirements.txt files."""

import re
import sys
from pathlib import Path
from typing import Dict


def normalize_name(name: str) -> str:
    """
    Normalize package/import names for comparison.
    
    Args:
        name: Package or import name
        
    Returns:
        Normalized name (lowercase with dashes)
    """
    return name.lower().replace('_', '-').replace('.', '-')


def parse_requirements(requirements_file: Path) -> Dict[str, str]:
    """
    Parse requirements.txt file.
    
    Args:
        requirements_file: Path to requirements.txt
        
    Returns:
        Dictionary mapping normalized package names to original requirement lines
        
    Raises:
        SystemExit: If file not found or cannot be read
    """
    requirements = {}
    
    try:
        with open(requirements_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Handle different requirement formats
                # Examples: package==1.0.0, package>=1.0.0, package, -e git+...
                if line.startswith('-e') or line.startswith('git+'):
                    # Editable installs or git URLs - try to extract package name
                    match = re.search(r'egg=([a-zA-Z0-9_-]+)', line)
                    if match:
                        package_name = match.group(1).lower().replace('_', '-')
                        requirements[package_name] = line
                    continue
                
                # Extract package name (before any version specifier)
                match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                if match:
                    package_name = match.group(1).lower().replace('_', '-')
                    requirements[package_name] = line
        
        return requirements
    except FileNotFoundError:
        print(f"❌ Requirements file not found: {requirements_file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading requirements file: {e}", file=sys.stderr)
        sys.exit(1)
