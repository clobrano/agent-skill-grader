"""Validation for YAML data."""
from typing import Any, Dict


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_item_dict(item_dict: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Validate a single item dictionary.

    Args:
        item_dict: Dictionary with item data.
        item_index: Index of item (for error reporting).

    Returns:
        Validated dictionary if all checks pass.

    Raises:
        ValidationError: If validation fails.
    """
    required_fields = ["score", "tokens"]

    # Check for missing required fields
    for field in required_fields:
        if field not in item_dict:
            raise ValidationError(
                f"Item {item_index}: missing required field '{field}'. "
                f"Each item must have: {', '.join(required_fields)}"
            )

    # Check that at least one prompt source is provided (inline or file)
    has_prompt = "prompt" in item_dict
    has_prompt_file = "prompt_file" in item_dict
    if not (has_prompt or has_prompt_file):
        raise ValidationError(
            f"Item {item_index}: must provide either 'prompt' or 'prompt_file'"
        )

    # Check that at least one golden_answer source is provided (inline or file)
    has_golden_answer = "golden_answer" in item_dict
    has_golden_answer_file = "golden_answer_file" in item_dict
    if not (has_golden_answer or has_golden_answer_file):
        raise ValidationError(
            f"Item {item_index}: must provide either 'golden_answer' or 'golden_answer_file'"
        )

    # Validate prompt field types
    if has_prompt and not isinstance(item_dict["prompt"], str):
        raise ValidationError(
            f"Item {item_index}: 'prompt' must be a string, "
            f"got {type(item_dict['prompt']).__name__}"
        )

    if has_prompt_file and not isinstance(item_dict["prompt_file"], str):
        raise ValidationError(
            f"Item {item_index}: 'prompt_file' must be a string, "
            f"got {type(item_dict['prompt_file']).__name__}"
        )

    # Validate golden_answer field types
    if has_golden_answer and not isinstance(item_dict["golden_answer"], str):
        raise ValidationError(
            f"Item {item_index}: 'golden_answer' must be a string, "
            f"got {type(item_dict['golden_answer']).__name__}"
        )

    if has_golden_answer_file and not isinstance(item_dict["golden_answer_file"], str):
        raise ValidationError(
            f"Item {item_index}: 'golden_answer_file' must be a string, "
            f"got {type(item_dict['golden_answer_file']).__name__}"
        )

    if not isinstance(item_dict["score"], (int, float)):
        raise ValidationError(
            f"Item {item_index}: 'score' must be numeric (int or float), "
            f"got {type(item_dict['score']).__name__}"
        )

    if not isinstance(item_dict["tokens"], int):
        raise ValidationError(
            f"Item {item_index}: 'tokens' must be an integer, "
            f"got {type(item_dict['tokens']).__name__}"
        )

    # Validate value ranges
    score = item_dict["score"]
    if score < 0 or score > 1:
        raise ValidationError(
            f"Item {item_index}: 'score' must be between 0 and 1 (inclusive), "
            f"got {score}"
        )

    tokens = item_dict["tokens"]
    if tokens < 0:
        raise ValidationError(
            f"Item {item_index}: 'tokens' must be non-negative, got {tokens}"
        )

    return item_dict
