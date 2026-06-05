"""Tests for YAML loading."""
import tempfile
from pathlib import Path

import pytest

from grader.yaml_loader import load_yaml
from grader.models import EvaluationDataset, EvaluationItem, EvaluationConfig


class TestYamlLoader:
    """Test YAML file loading."""

    def test_load_valid_yaml(self):
        """Valid YAML file is loaded correctly."""
        yaml_content = """
items:
  - prompt: "What is 2+2?"
    golden_answer: "4"
    score: 0
    tokens: 0
  - prompt: "What is 3+3?"
    golden_answer: "6"
    score: 0.8
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert isinstance(dataset, EvaluationDataset)
            assert len(dataset) == 2
            assert dataset[0].prompt == "What is 2+2?"
            assert dataset[0].golden_answer == "4"
            assert dataset[0].score == 0
            assert dataset[1].prompt == "What is 3+3?"
            assert dataset[1].score == 0.8
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_single_item(self):
        """YAML with single item loads correctly."""
        yaml_content = """
items:
  - prompt: "Question?"
    golden_answer: "Answer"
    score: 0.5
    tokens: 50
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert len(dataset) == 1
            assert dataset[0].score == 0.5
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_empty_items(self):
        """YAML with empty items list loads correctly."""
        yaml_content = "items: []\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert len(dataset) == 0
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file_raises_error(self):
        """Loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_yaml("/nonexistent/path/file.yaml")

    def test_load_malformed_yaml_raises_error(self):
        """Malformed YAML raises error."""
        yaml_content = """
items:
  - prompt: "Question?"
    golden_answer: "Answer
    score: 0.5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # YAML parsing error
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_missing_items_key_raises_error(self):
        """YAML missing 'items' key raises error."""
        yaml_content = "other_key: []\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises((KeyError, ValueError)):
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_items_not_list_raises_error(self):
        """YAML with non-list items value raises error."""
        yaml_content = "items: {}\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises((TypeError, ValueError)):
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_preserves_formatting(self):
        """Loaded YAML content can be written back with minimal diffs."""
        yaml_content = """items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
  - prompt: "Q2"
    golden_answer: "A2"
    score: 0.5
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            # Verify items were loaded
            assert len(dataset) == 2
            # The dataset should work with yaml_writer to preserve format
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_prompt_file(self):
        """YAML with prompt_file field reads content from external file."""
        # Create external prompt file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Question from file")
            prompt_file_path = f.name

        # Create YAML file referencing external prompt
        yaml_content = f"""
items:
  - prompt_file: "{prompt_file_path}"
    golden_answer: "Answer"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert len(dataset) == 1
            assert dataset[0].prompt == "Question from file"
            assert dataset[0].golden_answer == "Answer"
        finally:
            Path(yaml_path).unlink()
            Path(prompt_file_path).unlink()

    def test_load_yaml_with_golden_answer_file(self):
        """YAML with golden_answer_file field reads content from external file."""
        # Create external answer file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Answer from file")
            answer_file_path = f.name

        # Create YAML file referencing external answer
        yaml_content = f"""
items:
  - prompt: "Question?"
    golden_answer_file: "{answer_file_path}"
    score: 0.5
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert len(dataset) == 1
            assert dataset[0].prompt == "Question?"
            assert dataset[0].golden_answer == "Answer from file"
        finally:
            Path(yaml_path).unlink()
            Path(answer_file_path).unlink()

    def test_load_yaml_with_both_files(self):
        """YAML with both prompt_file and golden_answer_file reads both."""
        # Create external files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Prompt from file")
            prompt_file_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Answer from file")
            answer_file_path = f.name

        # Create YAML file referencing both
        yaml_content = f"""
items:
  - prompt_file: "{prompt_file_path}"
    golden_answer_file: "{answer_file_path}"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert len(dataset) == 1
            assert dataset[0].prompt == "Prompt from file"
            assert dataset[0].golden_answer == "Answer from file"
        finally:
            Path(yaml_path).unlink()
            Path(prompt_file_path).unlink()
            Path(answer_file_path).unlink()

    def test_load_yaml_mixed_inline_and_file(self):
        """YAML can mix inline and file-based values in different items."""
        # Create external file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("From file")
            file_path = f.name

        yaml_content = f"""
items:
  - prompt: "Inline prompt"
    golden_answer_file: "{file_path}"
    score: 0
    tokens: 0
  - prompt_file: "{file_path}"
    golden_answer: "Inline answer"
    score: 0.5
    tokens: 100
  - prompt: "Both inline prompt"
    golden_answer: "Both inline answer"
    score: 1.0
    tokens: 200
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert len(dataset) == 3
            assert dataset[0].prompt == "Inline prompt"
            assert dataset[0].golden_answer == "From file"
            assert dataset[1].prompt == "From file"
            assert dataset[1].golden_answer == "Inline answer"
            assert dataset[2].prompt == "Both inline prompt"
            assert dataset[2].golden_answer == "Both inline answer"
        finally:
            Path(yaml_path).unlink()
            Path(file_path).unlink()

    def test_load_yaml_prompt_file_not_found(self):
        """Loading YAML with nonexistent prompt_file raises error."""
        yaml_content = """
items:
  - prompt_file: "/nonexistent/prompt.txt"
    golden_answer: "Answer"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                load_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_golden_answer_file_not_found(self):
        """Loading YAML with nonexistent golden_answer_file raises error."""
        yaml_content = """
items:
  - prompt: "Question?"
    golden_answer_file: "/nonexistent/answer.txt"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            with pytest.raises(FileNotFoundError):
                load_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_prompt_file_precedence_over_inline(self):
        """prompt_file takes precedence if both prompt and prompt_file exist."""
        # Create external prompt file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("From file")
            prompt_file_path = f.name

        yaml_content = f"""
items:
  - prompt: "Inline prompt"
    prompt_file: "{prompt_file_path}"
    golden_answer: "Answer"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert dataset[0].prompt == "From file"
        finally:
            Path(yaml_path).unlink()
            Path(prompt_file_path).unlink()

    def test_load_yaml_golden_answer_file_precedence_over_inline(self):
        """golden_answer_file takes precedence if both exist."""
        # Create external answer file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("From file")
            answer_file_path = f.name

        yaml_content = f"""
items:
  - prompt: "Question?"
    golden_answer: "Inline answer"
    golden_answer_file: "{answer_file_path}"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert dataset[0].golden_answer == "From file"
        finally:
            Path(yaml_path).unlink()
            Path(answer_file_path).unlink()

    def test_load_yaml_missing_both_prompt_and_prompt_file(self):
        """Missing both prompt and prompt_file raises validation error."""
        yaml_content = """
items:
  - golden_answer: "Answer"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            from grader.validator import ValidationError
            with pytest.raises(ValidationError):
                load_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_load_yaml_missing_both_golden_answer_and_file(self):
        """Missing both golden_answer and golden_answer_file raises validation error."""
        yaml_content = """
items:
  - prompt: "Question?"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            from grader.validator import ValidationError
            with pytest.raises(ValidationError):
                load_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()


class TestYamlLoaderWithConfig:
    """Test YAML loading with config fields."""

    def test_load_yaml_with_model_field(self):
        """YAML with top-level model field loads correctly."""
        yaml_content = """
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert dataset.config is not None
            assert dataset.config.model == "claude-3-5-sonnet-20241022"
            assert dataset.config.agent_binary is None
            assert len(dataset) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_agent_binary_field(self):
        """YAML with top-level agent_binary field loads correctly."""
        yaml_content = """
agent_binary: "/path/to/agent"
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert dataset.config is not None
            assert dataset.config.agent_binary == "/path/to/agent"
            assert dataset.config.model is None
            assert len(dataset) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_both_config_fields(self):
        """YAML with both agent_binary and model loads correctly."""
        yaml_content = """
agent_binary: "/path/to/agent"
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert dataset.config is not None
            assert dataset.config.agent_binary == "/path/to/agent"
            assert dataset.config.model == "claude-3-5-sonnet-20241022"
            assert len(dataset) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_without_config_fields_backward_compat(self):
        """YAML without config fields (backward compat) has None config."""
        yaml_content = """
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert dataset.config is None
            assert len(dataset) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_empty_model_string_raises_error(self):
        """YAML with empty model string raises validation error."""
        yaml_content = """
model: ""
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_whitespace_model_raises_error(self):
        """YAML with whitespace-only model raises validation error."""
        yaml_content = """
model: "   "
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError):
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_with_config_and_multiple_items(self):
        """Config and items are both loaded correctly."""
        yaml_content = """
agent_binary: "/path/to/agent"
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
  - prompt: "Q2"
    golden_answer: "A2"
    score: 0.5
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            assert dataset.config.agent_binary == "/path/to/agent"
            assert dataset.config.model == "claude-3-5-sonnet-20241022"
            assert len(dataset) == 2
            assert dataset[0].prompt == "Q1"
            assert dataset[1].prompt == "Q2"
        finally:
            Path(temp_path).unlink()

    def test_load_yaml_preserves_config_with_file_references(self):
        """Config is preserved when items use file references."""
        # Create external file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Answer from file")
            answer_file_path = f.name

        yaml_content = f"""
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Question?"
    golden_answer_file: "{answer_file_path}"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name

        try:
            dataset = load_yaml(yaml_path)
            assert dataset.config is not None
            assert dataset.config.model == "claude-3-5-sonnet-20241022"
            assert dataset[0].golden_answer == "Answer from file"
        finally:
            Path(yaml_path).unlink()
            Path(answer_file_path).unlink()
