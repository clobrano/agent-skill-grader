"""Tests for CLI configuration parsing."""
import os
import tempfile
from pathlib import Path

import pytest

from grader.config import parse_args, Config


class TestConfigParsing:
    """Test CLI argument parsing."""

    def test_parse_args_with_valid_file(self):
        """Valid file path is parsed correctly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path])
            assert args.path == temp_path
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_default_model(self):
        """Default model is None (allows YAML or DEFAULT_MODEL precedence)."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path])
            assert args.model is None
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_custom_model(self):
        """Custom model flag is parsed correctly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path, "--model", "claude-3-opus-20250729"])
            assert args.model == "claude-3-opus-20250729"
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_default_verbosity(self):
        """Default verbosity is 'normal'."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path])
            assert args.verbosity == "normal"
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_quiet_verbosity(self):
        """Quiet verbosity flag is parsed correctly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path, "--verbosity", "quiet"])
            assert args.verbosity == "quiet"
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_verbose_verbosity(self):
        """Verbose verbosity flag is parsed correctly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path, "--verbosity", "verbose"])
            assert args.verbosity == "verbose"
        finally:
            os.unlink(temp_path)

    def test_parse_args_with_debug_verbosity(self):
        """Debug verbosity flag is parsed correctly."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            args = parse_args([temp_path, "--verbosity", "debug"])
            assert args.verbosity == "debug"
        finally:
            os.unlink(temp_path)

    def test_parse_args_missing_path_raises_error(self):
        """Missing required path argument raises error."""
        with pytest.raises(SystemExit):
            parse_args([])

    def test_parse_args_with_invalid_verbosity(self):
        """Invalid verbosity choice raises error."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            with pytest.raises(SystemExit):
                parse_args([temp_path, "--verbosity", "invalid"])
        finally:
            os.unlink(temp_path)


class TestConfigValidation:
    """Test configuration validation."""

    def test_config_file_exists(self):
        """File existence is validated."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            config = Config(path=temp_path, model=None, verbosity="normal")
            config.validate()
        finally:
            os.unlink(temp_path)

    def test_config_missing_file_raises_error(self):
        """Missing file raises error."""
        config = Config(
            path="/nonexistent/path/to/file.yaml",
            model=None,
            verbosity="normal"
        )
        with pytest.raises(FileNotFoundError):
            config.validate()

    def test_config_file_not_readable(self):
        """Non-readable file raises error."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            os.chmod(temp_path, 0o000)
            config = Config(path=temp_path, model=None, verbosity="normal")
            with pytest.raises((PermissionError, OSError)):
                config.validate()
        finally:
            os.chmod(temp_path, 0o644)
            os.unlink(temp_path)

    def test_config_stores_all_fields(self):
        """Config stores path, model, and verbosity."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            temp_path = f.name
        try:
            config = Config(path=temp_path, model="test-model", verbosity="debug")
            assert config.path == temp_path
            assert config.model == "test-model"
            assert config.verbosity == "debug"
        finally:
            os.unlink(temp_path)
