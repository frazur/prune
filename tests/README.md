# Prune Tests

Command-level integration tests for the prune CLI tool. ✅ **14 of 20 tests passing**

## Quick Start

```bash
# Install pytest
pip install pytest

# Run all tests
pytest tests/

# Run tests in VS Code Testing view (beaker icon in sidebar)
```

## What's Tested

These are **end-to-end command tests** that run the actual `prune` CLI commands:

✅ **Working Tests (14):**
- `prune init` command (5 tests)
  - Directory and config creation  
  - Default requirements detection
  - Update functionality
  - Error handling
- `prune verify` command (4 tests)
  - Package verification
  - Multiple source paths
  - Empty requirements
  - Python file discovery
- Edge cases (5 tests)
  - Relative imports
  - Standard library handling
  - Package mappings (PIL → Pillow)
  - Runtime dependencies (FastAPI)

⚠️ **Known Issues (6):**
- Config validation with stdin prompts
- CLI argument parsing edge cases

## Setup

Install pytest (development dependency):

```bash
pip install -e ".[dev]"
```

Or install pytest directly:

```bash
pip install pytest
```

## Running Tests

### From Command Line

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_prune_commands.py
```

Run specific test class:
```bash
pytest tests/test_prune_commands.py::TestPruneInit
```

Run specific test:
```bash
pytest tests/test_prune_commands.py::TestPruneInit::test_init_creates_prune_directory
```

Run only passing tests:
```bash
pytest tests/test_prune_commands.py::TestPruneInit -v
pytest tests/test_prune_commands.py::TestEdgeCases -v
pytest tests/test_prune_commands.py::TestPackageMappings -v
pytest tests/test_prune_commands.py::TestRuntimeDependencies -v
```

### From VS Code

1. **Enable Python Testing**:
   - The `.vscode/settings.json` is already configured for pytest
   - VS Code will automatically discover tests

2. **Run Tests**:
   - Open the Testing view (beaker icon in the sidebar, or `Ctrl+Shift+T`)
   - Click "Run All Tests" or run individual tests/classes
   - Tests will appear in the Test Explorer tree

3. **Debug Tests**:
   - Click the debug icon next to any test to run it in debug mode
   - Set breakpoints in test code or prune source code

4. **Watch Mode**:
   - Tests auto-discover when you save files (configured in settings)

## Test Structure

All tests use `subprocess` to execute the actual `prune` CLI commands, testing the tool end-to-end:

- **TestPruneInit**: Tests for `prune init` command
  - Directory creation
  - Config file generation
  - PyPI metadata fetching
  - Update functionality

- **TestPruneVerify**: Tests for `prune verify` command
  - Basic verification workflow
  - Multiple source paths
  - Custom config files
  - Output file generation

- **TestConfigValidation**: Configuration validation tests
  - Hash mismatch detection
  - Wrong requirements file detection

- **TestEdgeCases**: Edge cases and error handling
  - Empty files
  - Missing imports
  - Relative imports
  - Stdlib handling

- **TestPackageMappings**: Package name mapping tests
  - PIL → Pillow
  - Other non-obvious mappings

- **TestRuntimeDependencies**: Runtime dependency tests
  - FastAPI dependencies
  - Framework-specific requirements

## Test Isolation

Each test uses `tmp_path` fixture for complete isolation:
- No shared state between tests
- Clean temporary directories
- No pollution of actual project files

## Continuous Integration

Run tests on each change:
```bash
pytest --tb=short
```

Or use watch mode (requires pytest-watch):
```bash
pip install pytest-watch
ptw
```
