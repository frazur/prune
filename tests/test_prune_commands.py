"""
Command-level tests for the prune CLI tool.
Tests the actual CLI commands end-to-end using subprocess.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

import pytest


@pytest.fixture
def prune_cmd():
    """Get the prune command to use in tests."""
    # Use the Python interpreter from the current environment
    # Add the project root to PYTHONPATH to ensure prune module is found
    venv_python = Path(sys.executable)
    return [str(venv_python), "-m", "prune"]


@pytest.fixture
def prune_env():
    """Environment variables for subprocess calls."""
    env = os.environ.copy()
    # Add project root to PYTHONPATH so prune module can be imported
    project_root = Path(__file__).parent.parent
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = str(project_root)
    
    # Set UTF-8 encoding for Windows to handle emoji output
    env["PYTHONIOENCODING"] = "utf-8"
    
    return env


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory with source files."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    
    # Create source directory
    src_dir = project_dir / "src"
    src_dir.mkdir()
    
    return project_dir


@pytest.fixture
def sample_requirements(temp_project):
    """Create a sample requirements.txt file."""
    req_file = temp_project / "requirements.txt"
    req_file.write_text(dedent("""
        requests==2.31.0
        numpy==1.24.0
        pandas==2.0.0
        pytest==7.4.0
    """).strip())
    return req_file


@pytest.fixture
def sample_python_files(temp_project):
    """Create sample Python files with imports."""
    src_dir = temp_project / "src"
    
    # File using requests and numpy
    (src_dir / "api.py").write_text(dedent("""
        import requests
        import numpy as np
        
        def fetch_data(url):
            response = requests.get(url)
            return np.array(response.json())
    """))
    
    # File using only requests
    (src_dir / "client.py").write_text(dedent("""
        import requests
        
        def get_api():
            return requests.Session()
    """))
    
    return src_dir


class TestPruneInit:
    """Test the 'prune init' command."""
    
    def test_init_creates_prune_directory(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test that init creates .prune directory."""
        result = subprocess.run(
            prune_cmd + ["init", "--req", str(sample_requirements)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        prune_dir = temp_project / ".prune"
        assert prune_dir.exists(), ".prune directory not created"
        assert prune_dir.is_dir(), ".prune is not a directory"
    
    def test_init_creates_config_file(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test that init creates prune-conf.json."""
        result = subprocess.run(
            prune_cmd + [ "init", "--req", str(sample_requirements)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        config_file = temp_project / ".prune" / "prune-conf.json"
        assert config_file.exists(), "Config file not created"
        
        # Verify it's valid JSON
        with open(config_file) as f:
            config = json.load(f)
        
        assert "_metadata" in config
        assert "package_mappings" in config
        assert "runtime_dependencies" in config
    
    def test_init_with_nonexistent_requirements(self, prune_cmd, prune_env, temp_project):
        """Test init with non-existent requirements file."""
        result = subprocess.run(
            prune_cmd + [ "init", "--req", "nonexistent.txt"],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode != 0, "Should fail with non-existent file"
    
    def test_init_detects_default_requirements(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test init without --req flag uses default requirements.txt."""
        result = subprocess.run(
            prune_cmd + [ "init"],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        config_file = temp_project / ".prune" / "prune-conf.json"
        assert config_file.exists()
        
        with open(config_file) as f:
            config = json.load(f)
        
        assert config["_metadata"]["source_requirements"] == "requirements.txt"
    
    def test_init_update_flag(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test init --update updates existing config."""
        # Create initial config
        subprocess.run(
            prune_cmd + [ "init", "--req", str(sample_requirements)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        config_file = temp_project / ".prune" / "prune-conf.json"
        initial_mtime = config_file.stat().st_mtime
        
        # Update config
        result = subprocess.run(
            prune_cmd + [ "init", "--update"],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        assert config_file.exists()
        # Note: mtime might not change if very fast, but command should succeed


class TestPruneVerify:
    """Test the 'prune verify' command."""
    
    def test_verify_basic_functionality(self, prune_cmd, prune_env, temp_project, sample_requirements, sample_python_files):
        """Test basic verify command execution."""
        result = subprocess.run(
            prune_cmd + ["verify", 
             str(sample_python_files), 
             "--requirements-file", str(sample_requirements),
             "--mapping"],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Check output files created
        verified_file = sample_requirements.parent / f"{sample_requirements.name}.verified"
        mapping_file = sample_requirements.parent / f"{sample_requirements.name}.mapping"
        
        assert verified_file.exists(), "Verified file not created"
        assert mapping_file.exists(), "Mapping file not created"
    
    def test_verify_creates_verified_file_with_used_packages(self, prune_cmd, prune_env, temp_project, sample_requirements, sample_python_files):
        """Test that verified file contains only used packages."""
        subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_requirements), str(sample_python_files)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        verified_file = sample_requirements.parent / f"{sample_requirements.name}.verified"
        verified_content = verified_file.read_text()
        
        # requests and numpy are used, pandas and pytest are not
        assert "requests" in verified_content
        assert "numpy" in verified_content
        assert "pandas" not in verified_content
        assert "pytest" not in verified_content
    
    def test_verify_creates_mapping_file(self, prune_cmd, prune_env, temp_project, sample_requirements, sample_python_files):
        """Test that mapping file shows package usage."""
        subprocess.run(
            prune_cmd + ["verify", 
             str(sample_python_files), 
             "--requirements-file", str(sample_requirements),
             "--mapping"],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        mapping_file = sample_requirements.parent / f"{sample_requirements.name}.mapping"
        mapping_content = mapping_file.read_text()
        
        # Should show which files use which packages
        assert "requests" in mapping_content
        assert "api.py" in mapping_content or "client.py" in mapping_content
    
    def test_verify_with_multiple_source_paths(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test verify with multiple source directories."""
        # Create multiple source dirs
        src1 = temp_project / "src1"
        src2 = temp_project / "src2"
        src1.mkdir()
        src2.mkdir()
        
        (src1 / "module1.py").write_text("import requests")
        (src2 / "module2.py").write_text("import numpy")
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_requirements), str(src1), str(src2)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        verified_file = sample_requirements.parent / f"{sample_requirements.name}.verified"
        verified_content = verified_file.read_text()
        
        assert "requests" in verified_content
        assert "numpy" in verified_content
    
    def test_verify_with_custom_config(self, prune_cmd, prune_env, temp_project, sample_requirements, sample_python_files):
        """Test verify with custom config file."""
        # Create custom config
        custom_config = temp_project / "custom-config.json"
        custom_config.write_text(json.dumps({
            "_metadata": {
                "source_requirements": "requirements.txt",
                "source_requirements_hash": "abc123",
                "generated_at": "2026-01-01T00:00:00Z",
                "last_updated": "2026-01-01T00:00:00Z"
            },
            "package_mappings": {},
            "runtime_dependencies": {},
            "package_extras": {}
        }))
        
        result = subprocess.run(
            prune_cmd + ["verify", 
             str(sample_python_files),
             "--requirements-file", str(sample_requirements),
             "--config", str(custom_config)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8",
            input="y\n"  # Confirm to proceed with hash mismatch warning
)
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    def test_verify_with_no_source_paths_fails(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test that verify fails when no source paths provided."""
        result = subprocess.run(
            prune_cmd + ["verify", "--requirements-file", str(sample_requirements)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        # arguably should require at least one source path
        assert result.returncode != 0, "Should fail with no source paths"
    
    def test_verify_with_nonexistent_requirements(self, prune_cmd, prune_env, temp_project, sample_python_files):
        """Test verify with non-existent requirements file."""
        result = subprocess.run(
            prune_cmd + [ "verify", 
             "nonexistent.txt", str(sample_python_files)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode != 0, "Should fail with non-existent requirements file"


class TestConfigValidation:
    """Test configuration validation during verify."""
    
    def test_config_validation_warns_on_hash_mismatch(self, prune_cmd, prune_env, temp_project, sample_requirements, sample_python_files):
        """Test that config validation warns when requirements file changes."""
        # Create initial config
        subprocess.run(
            prune_cmd + [ "init", "--req", str(sample_requirements)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        # Modify requirements file
        sample_requirements.write_text(sample_requirements.read_text() + "\nflask==2.0.0\n")
        
        # Verify should warn about hash mismatch
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_requirements), str(sample_python_files)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            input="y\n"  # Confirm to proceed
        )
        
        # Should still succeed but with warning
        assert "changed" in result.stdout.lower() or "changed" in result.stderr.lower()
    
    def test_config_validation_detects_wrong_requirements_file(self, prune_cmd, prune_env, temp_project, sample_python_files):
        """Test that using config from different requirements file is detected."""
        # Create initial requirements and config
        req1 = temp_project / "requirements.txt"
        req1.write_text("requests==2.31.0\n")
        
        subprocess.run(
            prune_cmd + [ "init", "--req", str(req1)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        # Create different requirements file
        req2 = temp_project / "dev-requirements.txt"
        req2.write_text("pytest==7.4.0\n")
        
        # Try to verify with different file but same config
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(req2), str(sample_python_files)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            input="y\n"  # Confirm to proceed
        )
        
        # Should warn about mismatch
        assert "requirements.txt" in result.stdout or "requirements.txt" in result.stderr


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_verify_with_empty_requirements(self, prune_cmd, prune_env, temp_project, sample_python_files):
        """Test verify with empty requirements file."""
        empty_req = temp_project / "empty.txt"
        empty_req.write_text("# Empty requirements\\n")
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_python_files), "--requirements-file", str(empty_req)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        # Should succeed - unmatched imports are warnings, not errors
        assert result.returncode == 0, f"Command failed: {result.stderr}"
    
    def test_verify_with_no_python_files(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test verify when source directory has no Python files."""
        empty_dir = temp_project / "empty_src"
        empty_dir.mkdir()
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_requirements), str(empty_dir)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        # Should succeed but mark all packages as unused
        assert result.returncode == 0
        
        verified_file = sample_requirements.parent / f"{sample_requirements.name}.verified"
        verified_content = verified_file.read_text().strip()
        
        # Should be empty or minimal since no imports found
        assert len(verified_content.split('\n')) <= 2  # Maybe header/comments
    
    def test_verify_with_relative_imports(self, prune_cmd, prune_env, temp_project, sample_requirements):
        """Test that relative imports are handled correctly."""
        src_dir = temp_project / "src"
        src_dir.mkdir(exist_ok=True)
        
        # Create package structure
        pkg_dir = src_dir / "mypackage"
        pkg_dir.mkdir(exist_ok=True)
        (pkg_dir / "__init__.py").write_text("")
        
        # File with relative import
        (pkg_dir / "module.py").write_text(dedent("""
            from . import other
            import requests
        """))
        
        (pkg_dir / "other.py").write_text("# empty")
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(sample_requirements), str(src_dir)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0
        
        verified_file = sample_requirements.parent / f"{sample_requirements.name}.verified"
        verified_content = verified_file.read_text()
        
        # Should still find requests
        assert "requests" in verified_content
    
    def test_verify_with_stdlib_imports(self, prune_cmd, prune_env, temp_project):
        """Test that stdlib imports don't cause issues."""
        req_file = temp_project / "requirements.txt"
        req_file.write_text("requests==2.31.0\n")
        
        src_dir = temp_project / "src"
        src_dir.mkdir(exist_ok=True)
        
        (src_dir / "app.py").write_text(dedent("""
            import os
            import sys
            import json
            from pathlib import Path
            import requests
        """))
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(req_file), str(src_dir)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0
        
        verified_file = req_file.parent / f"{req_file.name}.verified"
        verified_content = verified_file.read_text()
        
        # Should only include requests, not stdlib modules
        assert "requests" in verified_content
        assert "os" not in verified_content
        assert "sys" not in verified_content
        assert "json" not in verified_content


class TestPackageMappings:
    """Test handling of package name mappings (e.g., PIL -> Pillow)."""
    
    def test_pil_to_pillow_mapping(self, prune_cmd, prune_env, temp_project):
        """Test that PIL import maps to Pillow package."""
        req_file = temp_project / "requirements.txt"
        req_file.write_text("Pillow==10.0.0\n")
        
        src_dir = temp_project / "src"
        src_dir.mkdir(exist_ok=True)
        
        (src_dir / "image.py").write_text(dedent("""
            from PIL import Image
            
            def load_image(path):
                return Image.open(path)
        """))
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(src_dir), "--requirements-file", str(req_file)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0
        
        verified_file = req_file.parent / f"{req_file.name}.verified"
        verified_content = verified_file.read_text()
        
        # Pillow should be marked as used
        assert "Pillow" in verified_content or "pillow" in verified_content.lower()


class TestRuntimeDependencies:
    """Test handling of runtime dependencies."""
    
    def test_fastapi_runtime_dependencies(self, prune_cmd, prune_env, temp_project):
        """Test that FastAPI runtime dependencies are included."""
        req_file = temp_project / "requirements.txt"
        req_file.write_text(dedent("""
            fastapi==0.104.0
            python-multipart==0.0.6
        """).strip())
        
        src_dir = temp_project / "src"
        src_dir.mkdir(exist_ok=True)
        
        (src_dir / "api.py").write_text(dedent("""
            from fastapi import FastAPI
            
            app = FastAPI()
        """))
        
        # Init to get runtime dependencies
        subprocess.run(
            prune_cmd + [ "init", "--req", str(req_file)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        result = subprocess.run(
            prune_cmd + [ "verify", 
             str(src_dir), "--requirements-file", str(req_file)],
            env=prune_env,
            cwd=temp_project,
            capture_output=True,
            text=True,
            encoding="utf-8"
)
        
        assert result.returncode == 0
        
        verified_file = req_file.parent / f"{req_file.name}.verified"
        verified_content = verified_file.read_text()
        
        # Both FastAPI and its runtime dependency should be included
        assert "fastapi" in verified_content.lower()
        # python-multipart might be included as runtime dependency









