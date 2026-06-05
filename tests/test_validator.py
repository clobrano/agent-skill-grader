"""Tests for YAML validation."""
import pytest

from grader.validator import validate_item_dict, ValidationError
from grader.models import EvaluationItem


class TestItemValidation:
    """Test item dictionary validation."""

    def test_valid_item_dict(self):
        """Valid item dictionary passes validation."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["prompt"] == "What is 2+2?"
        assert result["score"] == 0.5

    def test_validation_missing_prompt(self):
        """Missing prompt field raises validation error."""
        item_dict = {
            "golden_answer": "4",
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "prompt" in str(exc_info.value).lower()
        assert "0" in str(exc_info.value)  # item index

    def test_validation_missing_golden_answer(self):
        """Missing golden_answer field raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "golden_answer" in str(exc_info.value).lower()

    def test_validation_missing_score(self):
        """Missing score field raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "score" in str(exc_info.value).lower()

    def test_validation_missing_tokens(self):
        """Missing tokens field raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 0.5
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "tokens" in str(exc_info.value).lower()

    def test_validation_score_out_of_range_negative(self):
        """Score below 0 raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": -0.1,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "score" in str(exc_info.value).lower()

    def test_validation_score_out_of_range_high(self):
        """Score above 1 raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 1.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "score" in str(exc_info.value).lower()

    def test_validation_score_zero_valid(self):
        """Score of 0 is valid (ungraded)."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 0,
            "tokens": 0
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["score"] == 0

    def test_validation_score_one_valid(self):
        """Score of 1 is valid (perfect)."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 1,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["score"] == 1

    def test_validation_tokens_negative(self):
        """Negative tokens raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 0.5,
            "tokens": -10
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        assert "tokens" in str(exc_info.value).lower()

    def test_validation_error_includes_item_index(self):
        """ValidationError includes item index for debugging."""
        item_dict = {"prompt": "What is 2+2?"}
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=5)
        error_msg = str(exc_info.value)
        assert "5" in error_msg  # item index should be mentioned

    def test_validation_error_includes_field_name(self):
        """ValidationError includes field name."""
        item_dict = {"prompt": "What is 2+2?"}
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        error_msg = str(exc_info.value)
        # Should mention one of the missing required fields
        assert any(field in error_msg.lower() for field in ["golden_answer", "score", "tokens"])

    def test_validation_prompt_not_string(self):
        """Non-string prompt raises validation error."""
        item_dict = {
            "prompt": 123,
            "golden_answer": "4",
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError):
            validate_item_dict(item_dict, item_index=0)

    def test_validation_golden_answer_not_string(self):
        """Non-string golden_answer raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": 4,
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError):
            validate_item_dict(item_dict, item_index=0)

    def test_validation_score_not_numeric(self):
        """Non-numeric score raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": "0.5",
            "tokens": 100
        }
        with pytest.raises(ValidationError):
            validate_item_dict(item_dict, item_index=0)

    def test_validation_tokens_not_int(self):
        """Non-integer tokens raises validation error."""
        item_dict = {
            "prompt": "What is 2+2?",
            "golden_answer": "4",
            "score": 0.5,
            "tokens": 100.5
        }
        with pytest.raises(ValidationError):
            validate_item_dict(item_dict, item_index=0)

    def test_validation_with_prompt_file(self):
        """Valid item with prompt_file instead of prompt passes validation."""
        item_dict = {
            "prompt_file": "/path/to/prompt.txt",
            "golden_answer": "Answer",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["prompt_file"] == "/path/to/prompt.txt"

    def test_validation_with_golden_answer_file(self):
        """Valid item with golden_answer_file instead of golden_answer passes validation."""
        item_dict = {
            "prompt": "Question?",
            "golden_answer_file": "/path/to/answer.txt",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["golden_answer_file"] == "/path/to/answer.txt"

    def test_validation_with_both_files(self):
        """Valid item with both prompt_file and golden_answer_file passes validation."""
        item_dict = {
            "prompt_file": "/path/to/prompt.txt",
            "golden_answer_file": "/path/to/answer.txt",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        assert result["prompt_file"] == "/path/to/prompt.txt"
        assert result["golden_answer_file"] == "/path/to/answer.txt"

    def test_validation_missing_both_prompt_and_prompt_file(self):
        """Missing both prompt and prompt_file raises validation error."""
        item_dict = {
            "golden_answer": "Answer",
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        error_msg = str(exc_info.value).lower()
        assert "prompt" in error_msg

    def test_validation_missing_both_golden_answer_and_file(self):
        """Missing both golden_answer and golden_answer_file raises validation error."""
        item_dict = {
            "prompt": "Question?",
            "score": 0.5,
            "tokens": 100
        }
        with pytest.raises(ValidationError) as exc_info:
            validate_item_dict(item_dict, item_index=0)
        error_msg = str(exc_info.value).lower()
        assert "golden_answer" in error_msg

    def test_validation_prompt_file_takes_precedence(self):
        """prompt_file field is accepted when both prompt and prompt_file exist."""
        item_dict = {
            "prompt": "Inline",
            "prompt_file": "/path/to/prompt.txt",
            "golden_answer": "Answer",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        # Should pass validation (precedence handled in loader)
        assert "prompt_file" in result

    def test_validation_golden_answer_file_takes_precedence(self):
        """golden_answer_file field is accepted when both exist."""
        item_dict = {
            "prompt": "Question?",
            "golden_answer": "Inline",
            "golden_answer_file": "/path/to/answer.txt",
            "score": 0.5,
            "tokens": 100
        }
        result = validate_item_dict(item_dict, item_index=0)
        # Should pass validation (precedence handled in loader)
        assert "golden_answer_file" in result
