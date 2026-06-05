"""Tests for data models."""
import pytest

from grader.models import EvaluationItem, EvaluationDataset, EvaluationConfig


class TestEvaluationItem:
    """Test EvaluationItem model."""

    def test_create_item_with_all_fields(self):
        """Item can be created with all required fields."""
        item = EvaluationItem(
            prompt="What is 2+2?",
            golden_answer="4",
            score=0.9,
            tokens=150
        )
        assert item.prompt == "What is 2+2?"
        assert item.golden_answer == "4"
        assert item.score == 0.9
        assert item.tokens == 150

    def test_create_item_with_zero_score(self):
        """Item can have score of 0 (ungraded)."""
        item = EvaluationItem(
            prompt="What is 2+2?",
            golden_answer="4",
            score=0,
            tokens=0
        )
        assert item.score == 0
        assert item.tokens == 0

    def test_create_item_with_one_score(self):
        """Item can have score of 1 (perfect)."""
        item = EvaluationItem(
            prompt="What is 2+2?",
            golden_answer="4",
            score=1.0,
            tokens=100
        )
        assert item.score == 1.0

    def test_item_rejects_negative_score(self):
        """Negative score raises validation error."""
        with pytest.raises((ValueError, AssertionError)):
            EvaluationItem(
                prompt="What is 2+2?",
                golden_answer="4",
                score=-0.1,
                tokens=100
            )

    def test_item_rejects_score_above_one(self):
        """Score above 1.0 raises validation error."""
        with pytest.raises((ValueError, AssertionError)):
            EvaluationItem(
                prompt="What is 2+2?",
                golden_answer="4",
                score=1.1,
                tokens=100
            )

    def test_item_rejects_missing_prompt(self):
        """Missing prompt raises error."""
        with pytest.raises(TypeError):
            EvaluationItem(
                golden_answer="4",
                score=0.5,
                tokens=100
            )

    def test_item_rejects_missing_golden_answer(self):
        """Missing golden_answer raises error."""
        with pytest.raises(TypeError):
            EvaluationItem(
                prompt="What is 2+2?",
                score=0.5,
                tokens=100
            )

    def test_item_rejects_missing_score(self):
        """Missing score raises error."""
        with pytest.raises(TypeError):
            EvaluationItem(
                prompt="What is 2+2?",
                golden_answer="4",
                tokens=100
            )

    def test_item_rejects_negative_tokens(self):
        """Negative tokens raises error."""
        with pytest.raises((ValueError, AssertionError)):
            EvaluationItem(
                prompt="What is 2+2?",
                golden_answer="4",
                score=0.5,
                tokens=-10
            )


class TestEvaluationDataset:
    """Test EvaluationDataset model."""

    def test_create_empty_dataset(self):
        """Empty dataset can be created."""
        dataset = EvaluationDataset(items=[])
        assert len(dataset.items) == 0

    def test_create_dataset_with_items(self):
        """Dataset can be created with multiple items."""
        item1 = EvaluationItem(
            prompt="Q1", golden_answer="A1", score=0, tokens=0
        )
        item2 = EvaluationItem(
            prompt="Q2", golden_answer="A2", score=0.8, tokens=100
        )
        dataset = EvaluationDataset(items=[item1, item2])
        assert len(dataset.items) == 2
        assert dataset.items[0].prompt == "Q1"
        assert dataset.items[1].prompt == "Q2"

    def test_dataset_len(self):
        """Dataset length is correct."""
        items = [
            EvaluationItem(prompt=f"Q{i}", golden_answer=f"A{i}", score=0, tokens=0)
            for i in range(5)
        ]
        dataset = EvaluationDataset(items=items)
        assert len(dataset) == 5

    def test_dataset_indexing(self):
        """Dataset items can be accessed by index."""
        items = [
            EvaluationItem(prompt=f"Q{i}", golden_answer=f"A{i}", score=0, tokens=0)
            for i in range(3)
        ]
        dataset = EvaluationDataset(items=items)
        assert dataset[0].prompt == "Q0"
        assert dataset[1].prompt == "Q1"
        assert dataset[2].prompt == "Q2"

    def test_dataset_iteration(self):
        """Dataset items can be iterated."""
        items = [
            EvaluationItem(prompt=f"Q{i}", golden_answer=f"A{i}", score=0, tokens=0)
            for i in range(3)
        ]
        dataset = EvaluationDataset(items=items)
        prompts = [item.prompt for item in dataset]
        assert prompts == ["Q0", "Q1", "Q2"]

    def test_dataset_with_config(self):
        """Dataset can include config."""
        config = EvaluationConfig(
            agent_binary="/path/to/agent",
            model="claude-3-5-sonnet-20241022"
        )
        items = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0, tokens=0)
        ]
        dataset = EvaluationDataset(items=items, config=config)
        assert dataset.config == config
        assert dataset.config.agent_binary == "/path/to/agent"
        assert dataset.config.model == "claude-3-5-sonnet-20241022"

    def test_dataset_with_none_config(self):
        """Dataset can have None config (backward compatible)."""
        items = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0, tokens=0)
        ]
        dataset = EvaluationDataset(items=items, config=None)
        assert dataset.config is None

    def test_dataset_without_config_defaults_to_none(self):
        """Dataset config defaults to None when not provided."""
        items = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0, tokens=0)
        ]
        dataset = EvaluationDataset(items=items)
        assert dataset.config is None


class TestEvaluationConfig:
    """Test EvaluationConfig model."""

    def test_create_config_with_both_fields(self):
        """Config can be created with both agent_binary and model."""
        config = EvaluationConfig(
            agent_binary="/path/to/agent",
            model="claude-3-5-sonnet-20241022"
        )
        assert config.agent_binary == "/path/to/agent"
        assert config.model == "claude-3-5-sonnet-20241022"

    def test_create_config_with_agent_binary_only(self):
        """Config can have only agent_binary."""
        config = EvaluationConfig(agent_binary="/path/to/agent")
        assert config.agent_binary == "/path/to/agent"
        assert config.model is None

    def test_create_config_with_model_only(self):
        """Config can have only model."""
        config = EvaluationConfig(model="claude-3-5-sonnet-20241022")
        assert config.agent_binary is None
        assert config.model == "claude-3-5-sonnet-20241022"

    def test_create_config_with_neither_field(self):
        """Config can be created with no fields (all optional)."""
        config = EvaluationConfig()
        assert config.agent_binary is None
        assert config.model is None

    def test_config_rejects_empty_model_string(self):
        """Model field cannot be empty string."""
        with pytest.raises(ValueError):
            EvaluationConfig(model="")

    def test_config_rejects_whitespace_only_model(self):
        """Model field cannot be whitespace-only."""
        with pytest.raises(ValueError):
            EvaluationConfig(model="   ")

    def test_config_rejects_non_string_agent_binary(self):
        """agent_binary must be string if provided."""
        with pytest.raises(TypeError):
            EvaluationConfig(agent_binary=123)

    def test_config_rejects_non_string_model(self):
        """model must be string if provided."""
        with pytest.raises(TypeError):
            EvaluationConfig(model=456)

    def test_config_accepts_none_for_agent_binary(self):
        """agent_binary can be None explicitly."""
        config = EvaluationConfig(agent_binary=None, model="claude-3-5-sonnet-20241022")
        assert config.agent_binary is None
        assert config.model == "claude-3-5-sonnet-20241022"

    def test_config_accepts_none_for_model(self):
        """model can be None explicitly."""
        config = EvaluationConfig(agent_binary="/path/to/agent", model=None)
        assert config.agent_binary == "/path/to/agent"
        assert config.model is None
