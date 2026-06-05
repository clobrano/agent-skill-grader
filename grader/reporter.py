"""Report generation and statistics."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from grader.models import EvaluationDataset, EvaluationItem
from grader.score_updater import UpdateResult


@dataclass
class Report:
    """Summary report from evaluation run."""

    total_items: int
    num_updated: int
    before_avg_score: float
    before_min_score: float
    before_max_score: float
    after_avg_score: float
    after_min_score: float
    after_max_score: float
    total_tokens: int
    improvements: List[Dict[str, Any]] = field(default_factory=list)
    verbosity: str = "normal"

    def format(self) -> str:
        """Format report as human-readable string.

        Output varies by verbosity level:
        - quiet: minimal/no output
        - normal: summary statistics
        - verbose: summary + improvements
        - debug: all details

        Returns:
            Formatted report text.
        """
        if self.verbosity == "quiet":
            return ""

        lines = []
        lines.append("=" * 60)
        lines.append("Evaluation Report")
        lines.append("=" * 60)

        # Summary stats
        lines.append(f"\nTotal items processed: {self.total_items}")
        lines.append(f"Items updated: {self.num_updated}")
        lines.append(f"Total tokens used: {self.total_tokens}")

        # Score statistics
        lines.append("\nScore Statistics:")
        lines.append(f"  Before update:")
        lines.append(f"    Average: {self.before_avg_score:.3f}")
        lines.append(f"    Min: {self.before_min_score:.3f}")
        lines.append(f"    Max: {self.before_max_score:.3f}")
        lines.append(f"  After update:")
        lines.append(f"    Average: {self.after_avg_score:.3f}")
        lines.append(f"    Min: {self.after_min_score:.3f}")
        lines.append(f"    Max: {self.after_max_score:.3f}")

        # Improvements (verbose and higher)
        if self.verbosity in ("verbose", "debug") and self.improvements:
            lines.append("\nScore Improvements:")
            for imp in self.improvements:
                improvement = imp["new_score"] - imp["old_score"]
                lines.append(
                    f"  {imp['prompt'][:50]}: {imp['old_score']:.2f} → {imp['new_score']:.2f} "
                    f"(+{improvement:.2f}, {imp['tokens']} tokens)"
                )

        lines.append("=" * 60)
        return "\n".join(lines)


def generate_report(
    dataset: EvaluationDataset,
    update_results: List[UpdateResult],
    verbosity: str = "normal"
) -> Report:
    """Generate evaluation report.

    Args:
        dataset: Final dataset after updates.
        update_results: List of UpdateResult objects from scoring.
        verbosity: Verbosity level for formatting.

    Returns:
        Report with statistics and improvements.
    """
    total_items = len(dataset)
    num_updated = len(update_results)
    total_tokens = sum(u.new_tokens for u in update_results)

    # Calculate before statistics
    # Before = old scores from updates + unchanged items from dataset
    before_scores = []
    after_scores = []

    # Create a map of updated items
    updated_map = {u.updated_item.prompt: u for u in update_results}

    # For each item in final dataset, determine before/after
    for item in dataset:
        if item.prompt in updated_map:
            update = updated_map[item.prompt]
            before_scores.append(update.old_score)
            after_scores.append(update.new_score)
        else:
            # Item wasn't updated, so before and after are the same
            before_scores.append(item.score)
            after_scores.append(item.score)

    # Calculate statistics
    if before_scores:
        before_avg = sum(before_scores) / len(before_scores)
        before_min = min(before_scores)
        before_max = max(before_scores)
    else:
        before_avg = 0
        before_min = 0
        before_max = 0

    if after_scores:
        after_avg = sum(after_scores) / len(after_scores)
        after_min = min(after_scores)
        after_max = max(after_scores)
    else:
        after_avg = 0
        after_min = 0
        after_max = 0

    # Build improvements list
    improvements = []
    for update in update_results:
        improvements.append({
            "prompt": update.updated_item.prompt,
            "old_score": update.old_score,
            "new_score": update.new_score,
            "tokens": update.new_tokens,
        })

    return Report(
        total_items=total_items,
        num_updated=num_updated,
        before_avg_score=before_avg,
        before_min_score=before_min,
        before_max_score=before_max,
        after_avg_score=after_avg,
        after_min_score=after_min,
        after_max_score=after_max,
        total_tokens=total_tokens,
        improvements=improvements,
        verbosity=verbosity
    )
