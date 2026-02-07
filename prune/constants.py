"""Constants and default configurations for prune."""

# Directory and file configuration
PRUNE_DIR = ".prune"
PRUNE_CONFIG_FILE = "prune-conf.json"

# Common mappings between import names and package names
PACKAGE_MAPPINGS = {
    'PIL': 'Pillow',
    'cv2': 'opencv-python',
    'sklearn': 'scikit-learn',
    'yaml': 'PyYAML',
    'dotenv': 'python-dotenv',
    'dateutil': 'python-dateutil',
    'OpenSSL': 'pyOpenSSL',
    'serial': 'pyserial',
    'bs4': 'beautifulsoup4',
    'google': 'google-api-python-client',
    'jwt': 'PyJWT',
}

# Default runtime dependencies that are not directly imported but required by frameworks
# Format: {trigger_package: [required_dependencies]}
DEFAULT_RUNTIME_DEPENDENCIES = {
    'fastapi': ['python-multipart'],  # Required for OAuth2PasswordRequestForm and file uploads
    'uvicorn': ['uvloop', 'httptools'],  # Optional but recommended for performance
    'celery': ['redis', 'kombu'],  # Message broker dependencies
    'flask': ['werkzeug', 'jinja2'],  # Core dependencies
    'django': ['sqlparse', 'asgiref'],  # Core dependencies
    'pytest': ['pluggy', 'iniconfig'],  # Core dependencies
}

# Default extras configuration template
DEFAULT_EXTRAS_CONFIG = {
    "_comment": "Configuration for package extras and runtime dependencies",
    "_instructions": {
        "package_mappings": "Maps import names to package names (e.g., 'PIL' -> 'Pillow')",
        "runtime_dependencies": "Packages that trigger inclusion of other packages",
        "package_extras": "Specific extras to include for packages (e.g., 'fastapi[all]' installs extra dependencies)"
    },
    "package_mappings": PACKAGE_MAPPINGS,
    "runtime_dependencies": DEFAULT_RUNTIME_DEPENDENCIES,
    "package_extras": {
        "fastapi": ["all"],
        "uvicorn": ["standard"],
        "sqlalchemy": ["asyncio"],
        "requests": ["security", "socks"],
        "pandas": ["performance"],
        "pytest": ["testing"],
    }
}

# Standard library modules to skip during analysis
STDLIB_MODULES = {
    'sys', 'os', 'io', 'json', 're', 'time', 'datetime',
    'typing', 'collections', 'itertools', 'functools',
    'pathlib', 'logging', 'unittest', 'asyncio', 'abc',
    'enum', 'dataclasses', 'argparse', 'subprocess',
    'threading', 'multiprocessing', 'pickle', 'csv',
    'html', 'xml', 'urllib', 'http', 'socket', 'email',
    'base64', 'hashlib', 'hmac', 'secrets', 'uuid',
    'copy', 'pprint', 'warnings', 'traceback', 'inspect',
    'contextlib', 'tempfile', 'shutil', 'glob', 'fnmatch', 'ast'
}
