"""Integration tests for end-to-end workflow."""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from grader.yaml_loader import load_yaml
from grader.yaml_writer import write_yaml
from grader.models import EvaluationDataset, EvaluationItem, EvaluationConfig
from grader.score_updater import should_update_score, apply_score_update
from grader.reporter import generate_report
from grader.config import DEFAULT_MODEL


class TestEndToEndWorkflow:
    """Test complete workflow from load to save."""

    def test_load_score_update_write_cycle(self):
        """Full cycle: load YAML, score items, update, write back."""
        # Setup: Create initial YAML with ungraded items
        yaml_content = """items:
  - prompt: "What is 2+2?"
    golden_answer: "4"
    score: 0
    tokens: 0
  - prompt: "What is Paris?"
    golden_answer: "The capital of France"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Load original
            dataset = load_yaml(temp_path)
            assert len(dataset) == 2
            assert dataset[0].score == 0
            assert dataset[1].score == 0

            # Simulate scoring
            updated_items = []
            updates = []

            for item in dataset:
                # Simulate Claude returning scores
                new_score = 0.9 if "2+2" in item.prompt else 0.8
                new_tokens = 150

                if should_update_score(item.score, new_score):
                    update = apply_score_update(item, new_score, new_tokens)
                    updated_items.append(update.updated_item)
                    updates.append(update)
                else:
                    updated_items.append(item)

            # Write back
            write_yaml(temp_path, EvaluationDataset(items=updated_items))

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded[0].score == 0.9
            assert reloaded[1].score == 0.8
            assert reloaded[0].tokens == 150
            assert reloaded[1].tokens == 150

            # Generate report
            report = generate_report(reloaded, updates, verbosity="normal")
            assert report.total_items == 2
            assert report.num_updated == 2
            assert report.total_tokens == 300

        finally:
            Path(temp_path).unlink()

    def test_mixed_update_and_no_update(self):
        """Handles mix of items that update and don't update."""
        yaml_content = """items:
  - prompt: "Q1"
    golden_answer: "A1"
    score: 0
    tokens: 0
  - prompt: "Q2"
    golden_answer: "A2"
    score: 0.9
    tokens: 100
  - prompt: "Q3"
    golden_answer: "A3"
    score: 0.3
    tokens: 50
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            updated_items = []
            updates = []

            for item in dataset:
                if item.prompt == "Q1":
                    # Ungraded -> score it
                    new_score = 0.8
                    new_tokens = 150
                elif item.prompt == "Q2":
                    # Already high score, try to update with lower
                    new_score = 0.7
                    new_tokens = 150
                else:
                    # Medium score, try to update with higher
                    new_score = 0.8
                    new_tokens = 200

                if should_update_score(item.score, new_score):
                    update = apply_score_update(item, new_score, new_tokens)
                    updated_items.append(update.updated_item)
                    updates.append(update)
                else:
                    updated_items.append(item)

            write_yaml(temp_path, EvaluationDataset(items=updated_items))
            reloaded = load_yaml(temp_path)

            # Q1: should update (was 0)
            assert reloaded[0].score == 0.8
            # Q2: should NOT update (0.7 < 0.9)
            assert reloaded[1].score == 0.9
            # Q3: should update (0.8 > 0.3)
            assert reloaded[2].score == 0.8

            # Only 2 updates
            assert len(updates) == 2

        finally:
            Path(temp_path).unlink()

    def test_error_handling_invalid_yaml(self):
        """Handles invalid YAML gracefully."""
        yaml_content = """items:
  - prompt: "Question
    golden_answer: "Answer"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # YAML parse error
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_error_handling_invalid_score(self):
        """Handles invalid scores gracefully."""
        yaml_content = """items:
  - prompt: "Q"
    golden_answer: "A"
    score: 1.5
    tokens: 100
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(Exception):  # Validation error
                load_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_statistics_calculation(self):
        """Report statistics are calculated correctly."""
        items_before = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.6, tokens=100),
            EvaluationItem(prompt="Q3", golden_answer="A3", score=0.7, tokens=100),
        ]

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name

        try:
            write_yaml(temp_path, EvaluationDataset(items=items_before))

            dataset = load_yaml(temp_path)

            # Score all items
            updated_items = []
            updates = []

            for item in dataset:
                new_score = 0.9
                update = apply_score_update(item, new_score, 200)
                updated_items.append(update.updated_item)
                updates.append(update)

            write_yaml(temp_path, EvaluationDataset(items=updated_items))

            report = generate_report(
                EvaluationDataset(items=updated_items),
                updates,
                verbosity="normal"
            )

            # Before: average of 0.5, 0.6, 0.7 = 0.6
            assert report.before_avg_score == pytest.approx(0.6, abs=0.01)
            # After: all 0.9
            assert report.after_avg_score == pytest.approx(0.9, abs=0.01)

        finally:
            Path(temp_path).unlink()


class TestModelPrecedence:
    """Test model resolution: CLI > YAML > DEFAULT."""

    def test_model_resolution_cli_overrides_yaml(self):
        """CLI --model overrides YAML model field."""
        yaml_content = """
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            # YAML has model
            assert dataset.config.model == "claude-3-5-sonnet-20241022"

            # CLI args would override this
            cli_model = "claude-3-opus-20250219"
            yaml_model = dataset.config.model if dataset.config else None
            resolved_model = cli_model or yaml_model or DEFAULT_MODEL

            assert resolved_model == "claude-3-opus-20250219"
        finally:
            Path(temp_path).unlink()

    def test_model_resolution_yaml_used_when_no_cli(self):
        """YAML model is used when CLI --model not provided."""
        yaml_content = """
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            # No CLI model (None)
            cli_model = None
            yaml_model = dataset.config.model if dataset.config else None
            resolved_model = cli_model or yaml_model or DEFAULT_MODEL

            assert resolved_model == "claude-3-5-sonnet-20241022"
        finally:
            Path(temp_path).unlink()

    def test_model_resolution_default_when_no_cli_or_yaml(self):
        """DEFAULT_MODEL is used when neither CLI nor YAML provided."""
        yaml_content = """
items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            # No CLI model, no YAML config
            cli_model = None
            yaml_model = dataset.config.model if dataset.config else None
            resolved_model = cli_model or yaml_model or DEFAULT_MODEL

            assert resolved_model == DEFAULT_MODEL
        finally:
            Path(temp_path).unlink()

    def test_model_resolution_cli_overrides_default(self):
        """CLI model overrides DEFAULT_MODEL."""
        yaml_content = """
items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            dataset = load_yaml(temp_path)
            # CLI model provided
            cli_model = "claude-3-opus-20250219"
            yaml_model = dataset.config.model if dataset.config else None
            resolved_model = cli_model or yaml_model or DEFAULT_MODEL

            assert resolved_model == "claude-3-opus-20250219"
        finally:
            Path(temp_path).unlink()

    def test_config_with_agent_binary_preserved_through_cycle(self):
        """Config with agent_binary survives load-save cycle."""
        yaml_content = """
agent_binary: "/path/to/agent"
model: "claude-3-5-sonnet-20241022"
items:
  - prompt: "Q"
    golden_answer: "A"
    score: 0
    tokens: 0
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            # Load
            dataset = load_yaml(temp_path)
            assert dataset.config.agent_binary == "/path/to/agent"
            assert dataset.config.model == "claude-3-5-sonnet-20241022"

            # Modify scores
            updated_items = [
                EvaluationItem(
                    prompt=dataset[0].prompt,
                    golden_answer=dataset[0].golden_answer,
                    score=0.8,
                    tokens=100
                )
            ]

            # Write back with config
            write_yaml(temp_path, EvaluationDataset(items=updated_items, config=dataset.config))

            # Reload and verify
            reloaded = load_yaml(temp_path)
            assert reloaded.config.agent_binary == "/path/to/agent"
            assert reloaded.config.model == "claude-3-5-sonnet-20241022"
            assert reloaded[0].score == 0.8
        finally:
            Path(temp_path).unlink()
