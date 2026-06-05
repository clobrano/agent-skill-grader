"""Tests for conditional score update logic."""
import pytest

from grader.score_updater import should_update_score, apply_score_update, UpdateResult
from grader.models import EvaluationItem


class TestScoreUpdateDecision:
    """Test score update decision logic."""

    def test_should_update_when_score_is_zero(self):
        """Score should be updated if old score is 0."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 0.5
        assert should_update_score(old_item.score, new_score) is True

    def test_should_update_when_new_score_higher(self):
        """Score should be updated if new score is higher."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.3, tokens=50)
        new_score = 0.7
        assert should_update_score(old_item.score, new_score) is True

    def test_should_not_update_when_new_score_lower(self):
        """Score should not be updated if new score is lower."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.8, tokens=100)
        new_score = 0.5
        assert should_update_score(old_item.score, new_score) is False

    def test_should_not_update_when_scores_equal(self):
        """Score should not be updated if scores are equal."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=50)
        new_score = 0.5
        assert should_update_score(old_item.score, new_score) is False

    def test_update_from_zero_to_one(self):
        """Score can be updated from 0 to 1."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 1.0
        assert should_update_score(old_item.score, new_score) is True

    def test_update_from_low_to_high(self):
        """Score can be updated from low to high."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.1, tokens=10)
        new_score = 0.9
        assert should_update_score(old_item.score, new_score) is True

    def test_no_update_from_high_to_low(self):
        """Score is not updated from high to low."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.9, tokens=150)
        new_score = 0.1
        assert should_update_score(old_item.score, new_score) is False

    def test_zero_score_always_updates(self):
        """Zero score always triggers update."""
        test_cases = [0, 0.1, 0.5, 0.9, 1.0]
        for new_score in test_cases:
            assert should_update_score(0, new_score) is True


class TestApplyScoreUpdate:
    """Test applying score updates to items."""

    def test_apply_update_replaces_score(self):
        """Applying update replaces the score."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 0.75
        new_tokens = 200

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.score == 0.75

    def test_apply_update_replaces_tokens(self):
        """Applying update replaces the tokens."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)
        new_score = 0.8
        new_tokens = 250

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.tokens == 250

    def test_apply_update_preserves_prompt(self):
        """Update preserves the prompt."""
        old_item = EvaluationItem(prompt="My question", golden_answer="A", score=0, tokens=0)
        new_score = 0.5
        new_tokens = 100

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.prompt == "My question"

    def test_apply_update_preserves_golden_answer(self):
        """Update preserves the golden_answer."""
        old_item = EvaluationItem(prompt="Q", golden_answer="My answer", score=0, tokens=0)
        new_score = 0.5
        new_tokens = 100

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.golden_answer == "My answer"

    def test_update_result_tracks_change(self):
        """UpdateResult tracks whether score changed."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 0.8
        new_tokens = 200

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.was_updated is True
        assert result.old_score == 0
        assert result.new_score == 0.8
        assert result.old_tokens == 0
        assert result.new_tokens == 200

    def test_update_result_has_updated_item(self):
        """UpdateResult includes the updated item."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100)
        new_score = 0.9
        new_tokens = 300

        result = apply_score_update(old_item, new_score, new_tokens)
        assert isinstance(result.updated_item, EvaluationItem)
        assert result.updated_item.score == 0.9
        assert result.updated_item.tokens == 300

    def test_update_with_zero_new_tokens(self):
        """Update handles zero new tokens correctly."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 0.5
        new_tokens = 0

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.tokens == 0

    def test_update_with_large_token_count(self):
        """Update handles large token counts."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0, tokens=0)
        new_score = 0.8
        new_tokens = 50000

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.updated_item.tokens == 50000

    def test_update_result_represents_improvement(self):
        """UpdateResult correctly identifies improvements."""
        old_item = EvaluationItem(prompt="Q", golden_answer="A", score=0.3, tokens=100)
        new_score = 0.8
        new_tokens = 200

        result = apply_score_update(old_item, new_score, new_tokens)
        assert result.was_updated is True
        improvement = result.new_score - result.old_score
        assert improvement == 0.5

    def test_update_always_succeeds(self):
        """apply_score_update always succeeds with valid inputs."""
        for old_score in [0, 0.3, 0.5, 0.9]:
            for new_score in [0.1, 0.5, 0.9, 1.0]:
                old_item = EvaluationItem(prompt="Q", golden_answer="A", score=old_score, tokens=100)
                result = apply_score_update(old_item, new_score, 200)
                assert result.updated_item.score == new_score
                assert result.updated_item.tokens == 200
