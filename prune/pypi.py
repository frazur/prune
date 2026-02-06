"""PyPI metadata fetcher and dependency extractor."""

import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from .constants import PACKAGE_MAPPINGS
from .parser import normalize_name


def fetch_package_metadata(package_name: str) -> Optional[Dict]:
    """
    Fetch package metadata from PyPI.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Package metadata dictionary, or None if fetch fails
    """
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        request = Request(url, headers={'User-Agent': 'prune/1.0'})
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))
    except (URLError, HTTPError) as e:
        print(f"   ⚠️  Could not fetch metadata for {package_name}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"   ⚠️  Error processing {package_name}: {e}", file=sys.stderr)
        return None


def extract_dependencies_from_metadata(metadata: Dict) -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Extract dependencies and extras from PyPI metadata.
    
    Args:
        metadata: Package metadata from PyPI
        
    Returns:
        Tuple of (runtime_dependencies, extras_dict)
    """
    runtime_deps = []
    extras_dict = {}
    
    info = metadata.get('info', {})
    requires_dist = info.get('requires_dist', [])
    
    if not requires_dist:
        return runtime_deps, extras_dict
    
    # Parse requirements
    for req in requires_dist:
        # Skip if None
        if not req:
            continue
            
        # Parse requirement format: "package (>=version) ; extra == 'extra_name'"
        # Extract package name (before any space, semicolon, or comparison operator)
        match = re.match(r'^([a-zA-Z0-9_-]+)', req)
        if not match:
            continue
        
        dep_name = match.group(1)
        
        # Check if it's an extra dependency
        if ';' in req and 'extra ==' in req:
            # Extract extra name
            extra_match = re.search(r'extra\s*==\s*["\']([^"\']+)["\']', req)
            if extra_match:
                extra_name = extra_match.group(1)
                if extra_name not in extras_dict:
                    extras_dict[extra_name] = []
                extras_dict[extra_name].append(dep_name)
        else:
            # Regular runtime dependency (no extra condition)
            if 'extra ==' not in req:
                runtime_deps.append(dep_name)
    
    return runtime_deps, extras_dict


def create_config_from_requirements(requirements_file: Path, 
                                    requirements: Dict[str, str],
                                    output_path: Path | None = None) -> None:
    """
    Create configuration file by fetching metadata from PyPI.
    
    Args:
        requirements_file: Path to requirements.txt
        requirements: Parsed requirements dictionary
        output_path: Optional output path for config file
    """
    print(f"\n🌐 Fetching metadata from PyPI...")
    print("   This may take a few moments...\n")
    
    runtime_dependencies = {}
    package_extras = {}
    
    for idx, (package_name, _) in enumerate(requirements.items(), 1):
        print(f"   [{idx}/{len(requirements)}] Fetching {package_name}...", end='')
        
        metadata = fetch_package_metadata(package_name)
        
        if metadata:
            runtime_deps, extras_dict = extract_dependencies_from_metadata(metadata)
            
            # Filter runtime deps to only include those in requirements.txt
            filtered_runtime_deps = [
                dep for dep in runtime_deps 
                if normalize_name(dep) in requirements
            ]
            
            if filtered_runtime_deps:
                runtime_dependencies[package_name] = filtered_runtime_deps
                print(f" ✓ ({len(filtered_runtime_deps)} deps)")
            else:
                print(" ✓")
            
            # Store available extras
            if extras_dict:
                # Get commonly used extras
                common_extras = []
                for extra_name in ['all', 'full', 'standard', 'complete', 'asyncio', 'security']:
                    if extra_name in extras_dict:
                        common_extras.append(extra_name)
                
                if common_extras:
                    package_extras[package_name] = common_extras
        else:
            print(" ✗")
        
        # Small delay to be nice to PyPI
        time.sleep(0.1)
    
    # Build config
    config = {
        "_comment": "Configuration generated from PyPI metadata",
        "_generated_from": str(requirements_file),
        "_instructions": {
            "package_mappings": "Maps import names to package names (e.g., 'PIL' -> 'Pillow')",
            "runtime_dependencies": "Packages that trigger inclusion of other packages (from PyPI metadata)",
            "package_extras": "Recommended extras for packages (from PyPI metadata)"
        },
        "package_mappings": PACKAGE_MAPPINGS,
        "runtime_dependencies": runtime_dependencies,
        "package_extras": package_extras
    }
    
    # Write config or print to terminal
    if output_path:
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"\n✅ Created configuration file: {output_path}")
            print(f"   • {len(runtime_dependencies)} packages with runtime dependencies")
            print(f"   • {len(package_extras)} packages with recommended extras")
        except Exception as e:
            print(f"\n❌ Error creating config file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Print to terminal
        print(f"\n📄 Configuration:\n")
        print(json.dumps(config, indent=2))
        print(f"\n\n✅ Configuration generated")
        print(f"   • {len(runtime_dependencies)} packages with runtime dependencies")
        print(f"   • {len(package_extras)} packages with recommended extras")
