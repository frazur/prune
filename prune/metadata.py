"""Package metadata extraction from installed packages."""

import sys
from pathlib import Path
from typing import Dict, Set
from importlib.metadata import distributions, PackageNotFoundError


def get_top_level_imports(package_name: str) -> Set[str]:
    """
    Get top-level import names for a package from its metadata.
    
    Args:
        package_name: Name of the installed package
        
    Returns:
        Set of top-level import names (e.g., {'docx'} for python-docx)
    """
    try:
        # Try to find the distribution
        from importlib.metadata import distribution
        dist = distribution(package_name)
        
        # Read top_level.txt if it exists
        if dist.read_text('top_level.txt'):
            top_level = dist.read_text('top_level.txt')
            # Split by newlines and filter empty lines
            return set(line.strip() for line in top_level.splitlines() if line.strip())
    except (PackageNotFoundError, FileNotFoundError, Exception):
        pass
    
    return set()


def build_package_import_map() -> Dict[str, str]:
    """
    Build a mapping of import names to package names from installed packages.
    
    This scans all installed packages and creates a reverse mapping where
    the import name points to the package name. For example:
    {'docx': 'python-docx', 'PIL': 'Pillow', 'sklearn': 'scikit-learn'}
    
    Returns:
        Dictionary mapping import names to package names
    """
    import_to_package = {}
    
    try:
        for dist in distributions():
            package_name = dist.metadata['Name']
            
            # Get top-level imports from metadata
            top_levels = get_top_level_imports(package_name)
            
            for import_name in top_levels:
                # Only add if import name differs from package name
                # (normalized comparison)
                if import_name.lower().replace('_', '-') != package_name.lower().replace('_', '-'):
                    import_to_package[import_name] = package_name
    except Exception as e:
        print(f"   ⚠️  Warning: Could not scan installed packages: {e}", file=sys.stderr)
    
    return import_to_package


def get_package_for_import(import_name: str, installed_map: Dict[str, str], 
                          manual_mappings: Dict[str, str]) -> str:
    """
    Get package name for an import, checking manual mappings first, then installed packages.
    
    Args:
        import_name: The import name to look up
        installed_map: Mapping from installed packages (from build_package_import_map)
        manual_mappings: Manual mappings from configuration (higher priority)
        
    Returns:
        Package name or the import_name itself if no mapping found
    """
    # Manual mappings take precedence
    if import_name in manual_mappings:
        return manual_mappings[import_name]
    
    # Check installed packages
    if import_name in installed_map:
        return installed_map[import_name]
    
    # Default to import name
    return import_name
