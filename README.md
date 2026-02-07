# 🌿 Prune

**Python Requirements & Unused Node Eliminator**

Analyze your Python codebase to identify and eliminate unused dependencies in `requirements.txt`. Prune uses AST parsing to extract actual imports, matches them against your requirements, and generates verified dependency files with detailed usage mappings.

## ✨ Features

- 🔍 **AST-Based Analysis** - Accurately extracts imports from Python files without executing code
- 📦 **Smart Package Mapping** - Handles non-obvious mappings (PIL→Pillow, sklearn→scikit-learn)
- 🔧 **Runtime Dependencies** - Automatically includes framework dependencies not directly imported
- 🌐 **PyPI Integration** - Fetches package metadata to discover dependencies and extras
- 📊 **Detailed Reports** - Generates verified requirements and usage mapping files
- ⚡ **Zero False Positives** - Standard library detection prevents incorrect flagging

## 🚀 Installation

```bash
# Install from source (development mode)
git clone https://github.com/yourusername/prune.git
cd prune
pip install -e .
```

## 📖 Usage

### Initialize Configuration

Set up the `.prune` directory with configuration:

```bash
# Initialize from requirements.txt (if exists)
prune init

# Initialize from specific requirements file
prune init --req custom-requirements.txt

# Update existing configuration
prune init --update

# Update from specific file
prune init --update --req dev-requirements.txt
```

The `init` command creates a `.prune/prune-conf.json` file by fetching metadata from PyPI. This configuration improves verification accuracy by providing package mappings and runtime dependencies.

**Important:** The config is tied to the specific requirements file used during `init`. If you use a different requirements file during verification, prune will detect the mismatch and warn you.

### Basic Verification

Verify requirements against your codebase:

```bash
# Uses requirements.txt by default
prune verify ./app ./tests

# Or specify a different requirements file
prune verify ./app --requirements-file custom-requirements.txt
```

Generate detailed mapping files:

```bash
prune verify ./app --mapping
```

### Using Custom Configuration

By default, `verify` uses `.prune/prune-conf.json` if it exists. You can also specify a custom configuration:

```bash
prune verify ./app --config custom-config.json
```

## 📂 Output Files

### `requirements.txt.verified` (always generated)
Contains only the dependencies actually used in your codebase:
```
arguably>=1.2.0
requests==2.31.0
```

### `requirements.txt.mapping` (with `--mapping` flag)
Detailed mapping showing which files use each requirement:
```
================================================================================
USED REQUIREMENTS
================================================================================

arguably>=1.2.0
  → verify_requirements.py

================================================================================
UNUSED REQUIREMENTS
================================================================================

# 3 requirements not imported in any scanned Python file:

pandas==2.0.0
numpy==1.24.0
matplotlib==3.7.0
```

### `requirements.txt.unmatched-mapping` (with `--mapping` flag)
Shows imports that couldn't be matched to any requirement:
```
================================================================================
UNMATCHED IMPORTS
================================================================================

# 2 imports found in Python files but not in requirements.txt:

local_module
  → app/main.py
  → app/utils.py

my_package
  → tests/test_utils.py
```

## ⚙️ Configuration System

### Initialize Configuration

Run `init` to set up the `.prune` directory:

```bash
prune init
```

This creates `.prune/prune-conf.json` by fetching metadata from PyPI. The configuration is automatically used by `verify` and improves accuracy.

The generated configuration includes metadata tracking:

```json
{
  "_comment": "Configuration generated from PyPI metadata",
  "_metadata": {
    "source_requirements": "requirements.txt",
    "source_requirements_hash": "abc123...",
    "generated_at": "2026-02-07T10:30:00Z",
    "last_updated": "2026-02-07T10:30:00Z"
  },
  "package_mappings": {
    "PIL": "Pillow",
    "cv2": "opencv-python",
    "sklearn": "scikit-learn"
  },
  "runtime_dependencies": {
    "fastapi": ["python-multipart"],
    "uvicorn": ["uvloop", "httptools"]
  },
  "package_extras": {
    "fastapi": ["all"],
    "uvicorn": ["standard"]
  }
}
```

### Config Validation

Prune validates the configuration against your requirements file:

- **File mismatch**: If you run `prune verify ./app --requirements-file custom.txt` but the config was generated from `requirements.txt`, prune will abort with an error
- **File changed**: If `requirements.txt` has been modified since the config was generated, prune will warn you and ask for confirmation
- **Solution**: Run `prune init --update` to refresh the configuration

### Configuration Fields

- **`_metadata`** - Tracks source requirements file and hash for validation
- **`package_mappings`** - Maps import names to package names when they differ
- **`runtime_dependencies`** - Packages that trigger inclusion of other packages
- **`package_extras`** - Recommended extras for packages (e.g., `fastapi[all]`)

## 🛠️ Development

### Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Unix/macOS)
source .venv/bin/activate

# Install in development mode
pip install -e .
```

### Running Tests

```bash
# Test on the prune project itself (uses requirements.txt by default)
prune verify .

# Test with custom requirements file
prune verify . --requirements-file dev-requirements.txt
```

### Project Structure

```
prune/
├── prune/                      # Main package
│   ├── __init__.py            # Package initialization
│   ├── cli.py                 # CLI commands (arguably)
│   ├── core.py                # Verification logic
│   ├── analyzer.py            # AST import extraction
│   ├── parser.py              # Requirements parsing
│   ├── pypi.py                # PyPI metadata fetching
│   ├── config.py              # Configuration management
│   └── constants.py           # Mappings and defaults
├── pyproject.toml             # Package configuration
├── requirements.txt           # Project dependencies
└── .github/
    └── copilot-instructions.md  # AI agent guidance
```

## 🎯 How It Works

1. **Initialize** - Run `prune init` to fetch PyPI metadata and create `.prune/prune-conf.json`
2. **Parse Requirements** - Reads and normalizes package names from requirements.txt
3. **Scan Python Files** - Recursively finds all .py files in specified paths
4. **Extract Imports** - Uses AST to extract import statements without executing code
5. **Match Packages** - Matches imports to requirements using normalization and mappings
6. **Check Runtime Deps** - Includes framework dependencies based on configuration
7. **Generate Reports** - Creates .verified file (and optionally .mapping/.unmatched-mapping with `--mapping` flag)

## 📋 Common Patterns

### Adding Package Mappings

When imports don't match package names:

```python
PACKAGE_MAPPINGS = {
    'PIL': 'Pillow',           # from PIL import Image
    'cv2': 'opencv-python',    # import cv2
    'sklearn': 'scikit-learn', # from sklearn import ...
}
```

### Runtime Dependencies

Frameworks that require packages not directly imported:

```python
DEFAULT_RUNTIME_DEPENDENCIES = {
    'fastapi': ['python-multipart'],  # OAuth2PasswordRequestForm
    'uvicorn': ['uvloop', 'httptools'], # Performance
    'pytest': ['pluggy', 'iniconfig'],  # Core dependencies
}
```

## 🔧 Requirements

- Python 3.11 or higher
- `arguably` - CLI framework (automatically installed)

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 💡 Tips

- Run `prune init` first to set up configuration with PyPI metadata
- Run verification before committing to catch unused dependencies early
- The `.prune` directory is automatically used by verify (add to .gitignore if preferred)
- Use `--mapping` flag to generate detailed usage reports
- Review the `.mapping` file to understand dependency usage
- Check `.unmatched-mapping` for local modules or missing dependencies
- Add custom mappings for proprietary or uncommon packages
- Standard library modules are automatically excluded (no false positives)
- Update configuration with `prune init --update` when requirements change

## 🐛 Known Limitations

- Requires hardcoded standard library list (update when Python version changes)
- Dynamic imports (`importlib`) are not detected
- Conditional imports in try/except blocks are captured
- Does not detect indirect dependencies (sub-dependencies)
