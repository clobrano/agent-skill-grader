"""Tests for main orchestration."""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from main import main


class TestMainOrchestration:
    """Test main.py orchestration."""

    def test_main_with_valid_yaml_and_mocked_api(self):
        """Main processes valid YAML with mocked Claude API."""
        yaml_content = """items:
  - prompt: "What is 2+2?"
    golden_answer: "4"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Mock the Claude API
            mock_response = Mock()
            mock_response.content = [Mock(text="Score: 0.9")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)

            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.return_value = mock_response

                exit_code = main([temp_path])

            assert exit_code == 0

            # Verify file was updated
            from grader.yaml_loader import load_yaml
            updated = load_yaml(temp_path)
            assert updated[0].score == 0.9

        finally:
            Path(temp_path).unlink()

    def test_main_returns_zero_on_success(self):
        """Main returns 0 on successful completion."""
        yaml_content = """items: []"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            exit_code = main([temp_path])
            assert exit_code == 0
        finally:
            Path(temp_path).unlink()

    def test_main_returns_one_on_missing_file(self):
        """Main returns 1 if file doesn't exist."""
        exit_code = main(["/nonexistent/file.yaml"])
        assert exit_code == 1

    def test_main_returns_one_on_invalid_yaml(self):
        """Main returns 1 if YAML is invalid."""
        yaml_content = """items: {bad yaml"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            exit_code = main([temp_path])
            assert exit_code == 1
        finally:
            Path(temp_path).unlink()

    def test_main_with_verbosity_flag(self):
        """Main accepts verbosity flag."""
        yaml_content = """items: []"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            exit_code = main([temp_path, "--verbosity", "debug"])
            assert exit_code == 0
        finally:
            Path(temp_path).unlink()

    def test_main_with_model_flag(self):
        """Main accepts model flag."""
        yaml_content = """items: []"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            exit_code = main([temp_path, "--model", "claude-3-opus-20250729"])
            assert exit_code == 0
        finally:
            Path(temp_path).unlink()

    def test_main_processes_multiple_items(self):
        """Main processes multiple items correctly."""
        yaml_content = """items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
  - prompt: "Q2"
    golden_answer: "A2"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            mock_response = Mock()
            mock_response.content = [Mock(text="Score: 0.8")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)

            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.return_value = mock_response

                exit_code = main([temp_path])

            assert exit_code == 0

            # Both items should be updated
            from grader.yaml_loader import load_yaml
            updated = load_yaml(temp_path)
            assert len(updated) == 2
            assert updated[0].score == 0.8
            assert updated[1].score == 0.8

        finally:
            Path(temp_path).unlink()

    def test_main_respects_score_update_rules(self):
        """Main respects conditional score update rules."""
        yaml_content = """items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
  - prompt: "Q2"
    golden_answer: "A2"
    score: 0.9
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Mock returns 0.8 for both
            mock_response = Mock()
            mock_response.content = [Mock(text="Score: 0.8")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)

            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.return_value = mock_response

                exit_code = main([temp_path])

            assert exit_code == 0

            from grader.yaml_loader import load_yaml
            updated = load_yaml(temp_path)

            # Q1: should update (was 0)
            assert updated[0].score == 0.8
            # Q2: should NOT update (0.8 < 0.9)
            assert updated[1].score == 0.9

        finally:
            Path(temp_path).unlink()

    def test_main_returns_one_on_api_error(self):
        """Main returns 1 if API call fails."""
        yaml_content = """items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.side_effect = Exception("API error")

                exit_code = main([temp_path])

            assert exit_code == 1

        finally:
            Path(temp_path).unlink()
