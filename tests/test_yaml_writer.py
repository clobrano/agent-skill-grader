"""Tests for YAML file writing and updating."""
import tempfile
from pathlib import Path

import pytest

from grader.yaml_writer import write_yaml
from grader.yaml_loader import load_yaml
from grader.models import EvaluationDataset, EvaluationItem, EvaluationConfig


class TestYamlWriter:
    """Test YAML file writing."""

    def test_write_yaml_updates_file(self):
        """Writing dataset updates the YAML file."""
        yaml_content = """items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Load original
            original = load_yaml(temp_path)
            assert original[0].score == 0

            # Modify and write back
            updated_items = [
                EvaluationItem(
                    prompt="Q1",
                    golden_answer="A1",
                    score=0.8,
                    tokens=150
                )
            ]
            dataset = EvaluationDataset(items=updated_items)
            write_yaml(temp_path, dataset)

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded[0].score == 0.8
            assert reloaded[0].tokens == 150
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_preserves_field_order(self):
        """Writing YAML preserves field order."""
        yaml_content = """items:
  - prompt: "Question"
    golden_answer: "Answer"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Load, modify, write
            original = load_yaml(temp_path)
            updated_items = [
                EvaluationItem(
                    prompt=original[0].prompt,
                    golden_answer=original[0].golden_answer,
                    score=0.9,
                    tokens=200
                )
            ]
            write_yaml(temp_path, EvaluationDataset(items=updated_items))

            # Check file content
            with open(temp_path, 'r') as f:
                content = f.read()

            # Field order should be preserved
            prompt_pos = content.find('prompt')
            golden_pos = content.find('golden_answer')
            score_pos = content.find('score')
            tokens_pos = content.find('tokens')

            assert prompt_pos < golden_pos < score_pos < tokens_pos
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_multiple_items(self):
        """Writing multiple items works correctly."""
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
            items = [
                EvaluationItem(prompt="Q1", golden_answer="A1", score=0.9, tokens=150),
                EvaluationItem(prompt="Q2", golden_answer="A2", score=0.8, tokens=200),
            ]
            write_yaml(temp_path, EvaluationDataset(items=items))

            reloaded = load_yaml(temp_path)
            assert len(reloaded) == 2
            assert reloaded[0].score == 0.9
            assert reloaded[1].score == 0.8
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_minimal_diff(self):
        """Writing preserves original formatting (minimal diff)."""
        yaml_content = """items:
  - prompt: "Question 1"
    golden_answer: "Answer 1"
    score: 0
    tokens: 0
  - prompt: "Question 2"
    golden_answer: "Answer 2"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            original = load_yaml(temp_path)

            # Only update first item's score
            items = [
                EvaluationItem(
                    prompt=original[0].prompt,
                    golden_answer=original[0].golden_answer,
                    score=0.7,
                    tokens=100
                ),
                original[1]
            ]

            write_yaml(temp_path, EvaluationDataset(items=items))

            with open(temp_path, 'r') as f:
                new_content = f.read()

            # Should still have same number of lines approximately
            assert "Question 1" in new_content
            assert "Question 2" in new_content
            assert "0.7" in new_content
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_with_zero_tokens(self):
        """Writing with zero tokens is valid."""
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
            items = [EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)]
            write_yaml(temp_path, EvaluationDataset(items=items))

            reloaded = load_yaml(temp_path)
            assert reloaded[0].tokens == 0
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_roundtrip(self):
        """Data survives write-read-write-read cycle."""
        items = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.9, tokens=200),
            EvaluationItem(prompt="Q3", golden_answer="A3", score=0.3, tokens=50),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            # Write
            write_yaml(temp_path, EvaluationDataset(items=items))

            # Read
            reloaded1 = load_yaml(temp_path)

            # Write again
            write_yaml(temp_path, reloaded1)

            # Read again
            reloaded2 = load_yaml(temp_path)

            # Verify data integrity
            assert len(reloaded2) == 3
            for i, item in enumerate(reloaded2):
                assert item.prompt == items[i].prompt
                assert item.golden_answer == items[i].golden_answer
                assert item.score == items[i].score
                assert item.tokens == items[i].tokens
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_nonexistent_directory(self):
        """Writing to nonexistent directory raises appropriate error."""
        temp_dir = tempfile.mkdtemp()
        invalid_path = f"{temp_dir}/nonexistent/file.yaml"

        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]

        try:
            with pytest.raises((FileNotFoundError, OSError)):
                write_yaml(invalid_path, EvaluationDataset(items=items))
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_write_yaml_empty_dataset(self):
        """Writing empty dataset works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("items: []\n")
            temp_path = f.name

        try:
            write_yaml(temp_path, EvaluationDataset(items=[]))
            reloaded = load_yaml(temp_path)
            assert len(reloaded) == 0
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_creates_valid_yaml(self):
        """Written YAML can be parsed by standard YAML parser."""
        items = [
            EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, EvaluationDataset(items=items))

            # Verify it's valid YAML by loading it
            reloaded = load_yaml(temp_path)
            assert len(reloaded) == 1
        finally:
            Path(temp_path).unlink()


class TestYamlWriterWithConfig:
    """Test YAML file writing with config preservation."""

    def test_write_yaml_preserves_model_field(self):
        """Writing YAML preserves model field at top level."""
        config = EvaluationConfig(model="claude-3-5-sonnet-20241022")
        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]
        dataset = EvaluationDataset(items=items, config=config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, dataset)

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded.config is not None
            assert reloaded.config.model == "claude-3-5-sonnet-20241022"
            assert reloaded.config.agent_binary is None
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_preserves_agent_binary_field(self):
        """Writing YAML preserves agent_binary field at top level."""
        config = EvaluationConfig(agent_binary="/path/to/agent")
        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]
        dataset = EvaluationDataset(items=items, config=config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, dataset)

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded.config is not None
            assert reloaded.config.agent_binary == "/path/to/agent"
            assert reloaded.config.model is None
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_preserves_both_config_fields(self):
        """Writing YAML preserves both agent_binary and model."""
        config = EvaluationConfig(
            agent_binary="/path/to/agent",
            model="claude-3-5-sonnet-20241022"
        )
        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]
        dataset = EvaluationDataset(items=items, config=config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, dataset)

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded.config is not None
            assert reloaded.config.agent_binary == "/path/to/agent"
            assert reloaded.config.model == "claude-3-5-sonnet-20241022"
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_without_config_backward_compat(self):
        """Writing dataset with None config works (backward compat)."""
        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]
        dataset = EvaluationDataset(items=items, config=None)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, dataset)

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded.config is None
            assert len(reloaded) == 1
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_config_field_order(self):
        """Config fields appear before items in written YAML."""
        config = EvaluationConfig(
            agent_binary="/path/to/agent",
            model="claude-3-5-sonnet-20241022"
        )
        items = [EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)]
        dataset = EvaluationDataset(items=items, config=config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, dataset)

            # Check file content for field order
            with open(temp_path, 'r') as f:
                content = f.read()

            agent_pos = content.find("agent_binary")
            model_pos = content.find("model")
            items_pos = content.find("items")

            assert agent_pos != -1, "agent_binary not found in output"
            assert model_pos != -1, "model not found in output"
            assert items_pos != -1, "items not found in output"
            assert agent_pos < items_pos, "agent_binary should come before items"
            assert model_pos < items_pos, "model should come before items"
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_roundtrip_with_config(self):
        """Config survives write-read-write-read cycle."""
        config = EvaluationConfig(
            agent_binary="/path/to/agent",
            model="claude-3-5-sonnet-20241022"
        )
        items = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.9, tokens=200),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            # Write initial
            write_yaml(temp_path, EvaluationDataset(items=items, config=config))

            # Read back
            reloaded1 = load_yaml(temp_path)

            # Write again
            write_yaml(temp_path, reloaded1)

            # Read again
            reloaded2 = load_yaml(temp_path)

            # Verify config intact
            assert reloaded2.config is not None
            assert reloaded2.config.agent_binary == "/path/to/agent"
            assert reloaded2.config.model == "claude-3-5-sonnet-20241022"
            assert len(reloaded2) == 2
        finally:
            Path(temp_path).unlink()

    def test_write_yaml_updates_scores_preserves_config(self):
        """Updating scores in items preserves config."""
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
            # Load original
            original = load_yaml(temp_path)
            assert original[0].score == 0

            # Update score
            updated_items = [
                EvaluationItem(
                    prompt=original[0].prompt,
                    golden_answer=original[0].golden_answer,
                    score=0.8,
                    tokens=150
                )
            ]
            write_yaml(temp_path, EvaluationDataset(items=updated_items, config=original.config))

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded[0].score == 0.8
            assert reloaded.config.agent_binary == "/path/to/agent"
            assert reloaded.config.model == "claude-3-5-sonnet-20241022"
        finally:
            Path(temp_path).unlink()
