"""
Smoke test to verify basic project setup and imports.

This test ensures:
1. Project structure is correct
2. Packages are importable
3. Dependencies are installed
"""

import sys
from pathlib import Path


def test_python_version():
    """Verify Python version is 3.10+."""
    assert sys.version_info >= (3, 10), "Python 3.10+ is required"


def test_project_structure():
    """Verify key directories exist."""
    project_root = Path(__file__).parent.parent

    required_dirs = [
        "glcs",
        "glcs/core",
        "glcs/utils",
        "glcs/hierarchical",
        "glcs/api",
        "tests/unit",
        "tests/integration",
        "config",
        "docs"
    ]

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        assert full_path.exists(), f"Required directory missing: {dir_path}"
        assert full_path.is_dir(), f"Path is not a directory: {dir_path}"


def test_package_imports():
    """Verify all subpackages are importable."""
    import glcs
    import glcs.core
    import glcs.utils
    import glcs.hierarchical
    import glcs.api

    # All imports succeeded
    assert glcs is not None


def test_dependencies_installed():
    """Verify critical dependencies are available."""
    # Core dependencies
    import numpy
    import pydantic
    from dotenv import load_dotenv

    # Verify versions
    assert numpy.__version__.startswith('1.26'), "NumPy 1.26+ required"
    assert pydantic.__version__.startswith('2.'), "Pydantic 2.x required"


def test_init_files_exist():
    """Verify all __init__.py files exist."""
    project_root = Path(__file__).parent.parent

    init_files = [
        "glcs/__init__.py",
        "glcs/core/__init__.py",
        "glcs/utils/__init__.py",
        "glcs/hierarchical/__init__.py",
        "glcs/api/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py",
    ]

    for init_file in init_files:
        full_path = project_root / init_file
        assert full_path.exists(), f"Missing __init__.py: {init_file}"


def test_config_files_exist():
    """Verify configuration files are present."""
    project_root = Path(__file__).parent.parent

    config_files = [
        "pyproject.toml",
        ".gitignore",
        ".env.template",
        "README.md"
    ]

    for config_file in config_files:
        full_path = project_root / config_file
        assert full_path.exists(), f"Missing config file: {config_file}"


def test_readme_files_exist():
    """Verify documentation README files exist."""
    project_root = Path(__file__).parent.parent

    readme_files = [
        "README.md",
        "docs/README.md",
        "glcs/core/README.md",
        "tests/README.md"
    ]

    for readme in readme_files:
        full_path = project_root / readme
        assert full_path.exists(), f"Missing README: {readme}"
        assert full_path.stat().st_size > 0, f"Empty README: {readme}"


if __name__ == "__main__":
    # Run tests manually
    import pytest
    pytest.main([__file__, "-v"])
