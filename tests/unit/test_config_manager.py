"""
Unit tests for configuration manager.

Tests cover:
- Loading valid configurations
- Handling invalid configurations
- Configuration validation
- Nested value access
- Error handling

Author: PhD Project
Version: 0.1.0
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from glcs.utils.config_manager import (
    load_config,
    validate_config,
    get_config_value,
    save_config
)
from glcs.utils.exceptions import ConfigurationError


def test_load_config_success():
    """Test loading a valid configuration file."""
    # Use the actual config file from the project
    config = load_config("config/glcs_config.yaml")

    # Check required sections exist
    assert 'memory' in config
    assert 'consistency' in config
    assert 'encoder' in config
    assert 'parser' in config
    assert 'logging' in config

    # Check specific values
    assert config['memory']['vector_dimension'] == 768
    assert config['encoder']['model_name'] == "sentence-transformers/all-MiniLM-L6-v2"


def test_load_config_file_not_found():
    """Test loading a non-existent config file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        load_config("config/nonexistent_config.yaml")

    assert "not found" in str(exc_info.value).lower()


def test_load_config_invalid_yaml():
    """Test loading invalid YAML raises ConfigurationError."""
    # Create a temporary file with invalid YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content:\n  - broken\n  indentation")
        temp_path = f.name

    try:
        with pytest.raises(ConfigurationError) as exc_info:
            load_config(temp_path)
        assert "parse" in str(exc_info.value).lower()
    finally:
        Path(temp_path).unlink()


def test_validate_config_valid():
    """Test validating a valid configuration."""
    valid_config = {
        'memory': {
            'vector_dimension': 768,
            'similarity_threshold': 0.85,
            'initial_capacity': 1000
        },
        'consistency': {
            'direct_contradiction_threshold': 0.85,
            'confidence_threshold': 0.5
        },
        'encoder': {
            'model_name': 'test-model',
            'batch_size': 32
        },
        'parser': {
            'llm_provider': 'openai',
            'model': 'gpt-4',
            'max_retries': 3,
            'timeout': 30
        },
        'logging': {
            'level': 'INFO',
            'format': 'simple'
        }
    }

    # Should not raise
    assert validate_config(valid_config) is True


def test_validate_config_missing_section():
    """Test validation fails when required section is missing."""
    invalid_config = {
        'memory': {},
        # Missing 'consistency', 'encoder', 'parser', 'logging'
    }

    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(invalid_config)

    assert "missing" in str(exc_info.value).lower()


def test_validate_config_value_out_of_range():
    """Test validation fails when values are out of range."""
    invalid_config = {
        'memory': {
            'vector_dimension': 768,
            'similarity_threshold': 1.5,  # Out of range (should be 0.0-1.0)
        },
        'consistency': {},
        'encoder': {},
        'parser': {},
        'logging': {}
    }

    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(invalid_config)

    assert "out of range" in str(exc_info.value).lower()


def test_validate_config_none():
    """Test validation fails on None config."""
    with pytest.raises(ConfigurationError) as exc_info:
        validate_config(None)

    assert "none" in str(exc_info.value).lower()


def test_get_config_value_exists():
    """Test getting an existing nested config value."""
    config = {
        'memory': {
            'similarity_threshold': 0.85
        }
    }

    value = get_config_value(config, "memory.similarity_threshold")
    assert value == 0.85


def test_get_config_value_deep_nesting():
    """Test getting deeply nested config value."""
    config = {
        'level1': {
            'level2': {
                'level3': {
                    'value': 42
                }
            }
        }
    }

    value = get_config_value(config, "level1.level2.level3.value")
    assert value == 42


def test_get_config_value_default():
    """Test returning default when path doesn't exist."""
    config = {'memory': {}}

    value = get_config_value(config, "nonexistent.path", default=999)
    assert value == 999


def test_get_config_value_none_default():
    """Test returning None default when path doesn't exist."""
    config = {}

    value = get_config_value(config, "missing.key")
    assert value is None


def test_save_config():
    """Test saving configuration to file."""
    config = {
        'test_section': {
            'test_param': 'test_value'
        }
    }

    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name

    try:
        save_config(config, temp_path)

        # Load it back and verify
        with open(temp_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config == config
    finally:
        Path(temp_path).unlink()


def test_save_config_preserves_structure():
    """Test that save_config preserves nested structure."""
    # Create a valid config with all required sections
    config = {
        'memory': {
            'vector_dimension': 768,
            'similarity_threshold': 0.85,
            'nested': {
                'value': 42
            }
        },
        'consistency': {},
        'encoder': {},
        'parser': {},
        'logging': {}
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        temp_path = f.name

    try:
        save_config(config, temp_path)

        # Load it back using YAML directly (to avoid validation)
        with open(temp_path, 'r') as f:
            loaded_config = yaml.safe_load(f)

        assert loaded_config['memory']['vector_dimension'] == 768
        assert loaded_config['memory']['nested']['value'] == 42
    finally:
        Path(temp_path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
