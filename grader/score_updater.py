"""Conditional score update logic and token tracking."""
from dataclasses import dataclass

from grader.models import EvaluationItem


@dataclass
class UpdateResult:
    """Result of applying a score update."""

    updated_item: EvaluationItem
    was_updated: bool
    old_score: float
    new_score: float
    old_tokens: int
    new_tokens: int


def should_update_score(old_score: float, new_score: float) -> bool:
    """Determine if score should be updated.

    Rules:
    - If old_score is 0 (ungraded): always update
    - If old_score > 0: only update if new_score is higher

    Args:
        old_score: Current score (0-1).
        new_score: New score from Claude (0-1).

    Returns:
        True if score should be updated, False otherwise.
    """
    if old_score == 0:
        return True
    return new_score > old_score


def apply_score_update(
    item: EvaluationItem,
    new_score: float,
    new_tokens: int
) -> UpdateResult:
    """Apply a score update to an item.

    Always updates the item with new score and tokens.
    Caller is responsible for checking should_update_score() first
    if conditional logic is needed.

    Args:
        item: Original evaluation item.
        new_score: New score to apply (0-1).
        new_tokens: Tokens consumed in this evaluation run.

    Returns:
        UpdateResult with updated item and metadata.
    """
    old_score = item.score
    old_tokens = item.tokens

    updated_item = EvaluationItem(
        prompt=item.prompt,
        golden_answer=item.golden_answer,
        score=new_score,
        tokens=new_tokens
    )

    was_updated = (old_score != new_score) or (old_tokens != new_tokens)

    return UpdateResult(
        updated_item=updated_item,
        was_updated=was_updated,
        old_score=old_score,
        new_score=new_score,
        old_tokens=old_tokens,
        new_tokens=new_tokens
    )
