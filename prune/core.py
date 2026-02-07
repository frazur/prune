"""Core verification logic for requirements matching."""

import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

from .analyzer import extract_imports_from_file, find_python_files
from .config import load_config
from .constants import STDLIB_MODULES, PRUNE_DIR, PRUNE_CONFIG_FILE
from .parser import normalize_name, parse_requirements


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Hex string of the file hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_config_against_requirements(config: Dict, requirements_file: Path, config_file: Optional[Path]) -> None:
    """
    Validate that config metadata matches the requirements file being verified.
    
    Args:
        config: Loaded configuration dictionary
        requirements_file: Path to requirements file being verified
        config_file: Path to config file (if explicitly provided)
        
    Raises:
        SystemExit: If validation fails
    """
    metadata = config.get('_metadata', {})
    
    # If no metadata, it's an old/manual config - just warn
    if not metadata:
        if not config_file:  # Only warn for auto-loaded configs
            print("⚠️  Warning: Config has no metadata (may be outdated or manually created)")
            print("   Consider running: prune init --update\n")
        return
    
    source_req_name = metadata.get('source_requirements', '')
    source_req_hash = metadata.get('source_requirements_hash', '')
    
    # Check 1: Requirements file name mismatch
    if source_req_name and source_req_name != requirements_file.name:
        print(f"❌ Error: Config mismatch detected", file=sys.stderr)
        print(f"   Config was generated from: {source_req_name}", file=sys.stderr)
        print(f"   But you're verifying against: {requirements_file.name}", file=sys.stderr)
        
        if config_file:
            # Explicit config file - warn but allow
            print(f"\n   ⚠️  You're using an explicit --config flag", file=sys.stderr)
            print(f"   Results may be inaccurate!", file=sys.stderr)
            response = input("   Continue anyway? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                print("\n❌ Verification cancelled", file=sys.stderr)
                sys.exit(1)
            print()
        else:
            # Auto-loaded config - hard error
            print(f"\n   Fix: Run 'prune init --req {requirements_file.name}' to generate matching config", file=sys.stderr)
            sys.exit(1)
    
    # Check 2: Requirements file content has changed
    if source_req_hash and requirements_file.exists():
        current_hash = calculate_file_hash(requirements_file)
        if current_hash != source_req_hash:
            print(f"⚠️  Warning: {requirements_file.name} has changed since config was generated", file=sys.stderr)
            print(f"   Config may be outdated and results could be inaccurate", file=sys.stderr)
            print(f"\n   Recommended: Run 'prune init --update' to refresh config", file=sys.stderr)
            response = input("   Continue anyway? [y/N]: ").strip().lower()
            if response not in ['y', 'yes']:
                print("\n❌ Verification cancelled", file=sys.stderr)
                sys.exit(1)
            print()


def match_import_to_package(import_name: str, 
                            requirements: Dict[str, str], 
                            package_mappings: Dict[str, str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Match an import name to a package in requirements.
    
    Args:
        import_name: Name of the imported module
        requirements: Parsed requirements dictionary
        package_mappings: Import to package name mappings
        
    Returns:
        Tuple of (package_name, requirement_line) or (None, None) if not found
    """
    # First check if there's a known mapping
    if import_name in package_mappings:
        mapped_name = normalize_name(package_mappings[import_name])
        if mapped_name in requirements:
            return mapped_name, requirements[mapped_name]
    
    # Try direct match with normalization
    normalized_import = normalize_name(import_name)
    if normalized_import in requirements:
        return normalized_import, requirements[normalized_import]
    
    # Try partial match (e.g., 'requests' matches 'requests-toolbelt')
    for pkg_name in requirements:
        if normalized_import in pkg_name or pkg_name in normalized_import:
            return pkg_name, requirements[pkg_name]
    
    return None, None


def verify_requirements(requirements_file: Path, 
                       source_paths: List[Path], 
                       config_file: Optional[Path] = None,
                       generate_mapping: bool = False) -> None:
    """
    Main verification logic to match requirements against imports.
    
    Args:
        requirements_file: Path to requirements.txt
        source_paths: List of source paths to scan
        config_file: Optional configuration file path
        generate_mapping: Whether to generate .mapping and .unmatched-mapping files
    """
    # Check if .prune directory exists (helpful but not required)
    prune_dir = Path.cwd() / PRUNE_DIR
    if not prune_dir.exists() and not config_file:
        print("💡 Tip: Run 'prune init' to create a .prune directory with configuration")
        print("   This will improve accuracy by fetching metadata from PyPI\n")
    
    # Load configuration
    config = load_config(config_file)
    
    # Validate config against requirements file
    validate_config_against_requirements(config, requirements_file, config_file)
    
    package_mappings = config.get('package_mappings', {})
    runtime_dependencies = config.get('runtime_dependencies', {})
    package_extras = config.get('package_extras', {})
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        sys.exit(1)
    
    # Validate all source paths
    for source_path in source_paths:
        if not source_path.exists():
            print(f"❌ Source path not found: {source_path}")
            sys.exit(1)
    
    print(f"📋 Parsing requirements from: {requirements_file}")
    requirements = parse_requirements(requirements_file)
    print(f"   Found {len(requirements)} packages in requirements.txt")
    
    print(f"\n🔍 Scanning Python files in: {', '.join(str(p) for p in source_paths)}")
    python_files = []
    for source_path in source_paths:
        python_files.extend(find_python_files(source_path))
    print(f"   Found {len(python_files)} Python files")
    
    print("\n📦 Analyzing imports...")
    all_imports: Set[str] = set()
    file_imports: Dict[Path, Set[str]] = {}
    
    for py_file in python_files:
        imports = extract_imports_from_file(py_file)
        file_imports[py_file] = imports
        all_imports.update(imports)
    
    print(f"   Found {len(all_imports)} unique imports")
    
    print("\n🔗 Matching imports to requirements...")
    used_requirements: Dict[str, str] = {}  # package_name -> requirement_line
    package_to_files: Dict[str, List[Path]] = defaultdict(list)  # package_name -> files using it
    unmatched_imports: Set[str] = set()
    unmatched_to_files: Dict[str, List[Path]] = defaultdict(list)  # unmatched import -> files using it
    
    for py_file, imports in file_imports.items():
        for import_name in imports:
            # Skip standard library modules
            if import_name in STDLIB_MODULES:
                continue
            
            package_name, requirement_line = match_import_to_package(
                import_name, requirements, package_mappings
            )
            
            if package_name and requirement_line:
                used_requirements[package_name] = requirement_line
                package_to_files[package_name].append(py_file)
            else:
                unmatched_imports.add(import_name)
                unmatched_to_files[import_name].append(py_file)
    
    print(f"   Matched {len(used_requirements)} requirements to imports")
    
    # Check for runtime dependencies
    print("\n🔧 Checking for runtime dependencies...")
    runtime_added = {}
    for trigger_pkg, runtime_deps in runtime_dependencies.items():
        # Check if the trigger package is used
        trigger_normalized = normalize_name(trigger_pkg)
        if trigger_normalized in used_requirements or any(
            normalize_name(imp) == trigger_normalized for imp in all_imports
        ):
            for runtime_dep in runtime_deps:
                runtime_normalized = normalize_name(runtime_dep)
                # Check if runtime dependency exists in requirements
                if runtime_normalized in requirements:
                    if runtime_normalized not in used_requirements:
                        used_requirements[runtime_normalized] = requirements[runtime_normalized]
                        runtime_added[runtime_normalized] = trigger_pkg
                        print(f"   + Added {runtime_dep} (runtime dependency for {trigger_pkg})")
    
    # Check for package extras recommendations
    if package_extras:
        print("\n📦 Checking for recommended package extras...")
        for pkg_name, extras_list in package_extras.items():
            pkg_normalized = normalize_name(pkg_name)
            if pkg_normalized in used_requirements:
                extras_str = ",".join(extras_list)
                print(f"   ℹ️  Consider using {pkg_name}[{extras_str}] for additional features")
    
    # Write verified requirements
    output_verified = requirements_file.parent / f"{requirements_file.name}.verified"
    with open(output_verified, 'w', encoding='utf-8') as f:
        for package_name in sorted(used_requirements.keys()):
            f.write(used_requirements[package_name] + '\n')
    
    print(f"\n✅ Created: {output_verified}")
    print(f"   Contains {len(used_requirements)} verified dependencies")
    
    # Write mapping file (only if requested)
    if not generate_mapping:
        # Skip mapping generation, jump to reporting
        unused = set(requirements.keys()) - set(used_requirements.keys())
        if unused:
            print(f"\n⚠️  Unused requirements ({len(unused)}):")
            for pkg in sorted(unused):
                print(f"   - {requirements[pkg]}")
        
        if unmatched_imports:
            print(f"\n⚠️  Unmatched imports ({len(unmatched_imports)}):")
            print("   These imports couldn't be matched to requirements.txt entries.")
            print("   They might be local modules or missing from requirements.txt:")
            for imp in sorted(unmatched_imports):
                print(f"   - {imp}")
            print("\n   💡 Use --mapping flag to generate detailed mapping files")
        
        print("\n✨ Done!")
        return
    
    # Generate mapping files
    output_mapping = requirements_file.parent / f"{requirements_file.name}.mapping"
    with open(output_mapping, 'w', encoding='utf-8') as f:
        f.write("# Mapping of requirements to files that use them\n")
        f.write("# Format: <requirement> => <files>\n\n")
        
        f.write("=" * 80 + "\n")
        f.write("USED REQUIREMENTS\n")
        f.write("=" * 80 + "\n\n")
        
        for package_name in sorted(used_requirements.keys()):
            f.write(f"{used_requirements[package_name]}\n")
            files = sorted(package_to_files[package_name])
            if files:
                for file in files:
                    # Make path relative to one of the source paths for readability
                    rel_path = file
                    for source_path in source_paths:
                        try:
                            rel_path = file.relative_to(source_path)
                            break
                        except ValueError:
                            continue
                    f.write(f"  → {rel_path}\n")
            elif package_name in runtime_added:
                f.write(f"  → [Runtime dependency for {runtime_added[package_name]}]\n")
            f.write("\n")
        
        # Add unused requirements section
        unused = set(requirements.keys()) - set(used_requirements.keys())
        if unused:
            f.write("\n" + "=" * 80 + "\n")
            f.write("UNUSED REQUIREMENTS\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"# {len(unused)} requirements not imported in any scanned Python file:\n\n")
            for package_name in sorted(unused):
                f.write(f"{requirements[package_name]}\n")
    
    print(f"✅ Created: {output_mapping}")
    
    # Write unmatched imports mapping file
    if unmatched_imports:
        output_unmatched = requirements_file.parent / f"{requirements_file.name}.unmatched-mapping"
        with open(output_unmatched, 'w', encoding='utf-8') as f:
            f.write("# Imports that couldn't be matched to requirements.txt entries\n")
            f.write("# These might be local modules or missing from requirements.txt\n\n")
            
            for import_name in sorted(unmatched_imports):
                f.write(f"• {import_name}\n")
                files = sorted(set(unmatched_to_files[import_name]))
                for file in files:
                    # Make path relative to one of the source paths for readability
                    rel_path = file
                    for source_path in source_paths:
                        try:
                            rel_path = file.relative_to(source_path)
                            break
                        except ValueError:
                            continue
                    f.write(f"  → {rel_path}: import {import_name}\n")
        
        print(f"✅ Created: {output_unmatched}")
    
    # Report unused requirements
    unused = set(requirements.keys()) - set(used_requirements.keys())
    if unused:
        print(f"\n⚠️  Unused requirements ({len(unused)}):")
        for pkg in sorted(unused):
            print(f"   - {requirements[pkg]}")
    
    # Report unmatched imports
    if unmatched_imports:
        print(f"\n⚠️  Unmatched imports ({len(unmatched_imports)}):")
        print("   These imports couldn't be matched to requirements.txt entries.")
        print("   They might be local modules or missing from requirements.txt:")
        for imp in sorted(unmatched_imports):
            print(f"   - {imp}")
        print(f"   (See {output_unmatched.name} for details)")
    
    print("\n✨ Done!")
