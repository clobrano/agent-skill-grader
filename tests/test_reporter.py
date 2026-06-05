"""Tests for report generation."""
import pytest

from grader.reporter import generate_report, Report
from grader.models import EvaluationDataset, EvaluationItem
from grader.score_updater import UpdateResult


class TestReportGeneration:
    """Test report generation."""

    def test_report_with_no_updates(self):
        """Report handles dataset with no updates."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.8, tokens=150),
        ])

        update_results = []

        report = generate_report(dataset, update_results, verbosity="normal")

        assert report.total_items == 2
        assert report.num_updated == 0
        assert report.total_tokens == 0

    def test_report_with_single_update(self):
        """Report handles single score update."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
        ])

        old_item = EvaluationItem(prompt="Q1", golden_answer="A1", score=0, tokens=0)
        new_item = EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100)
        update = UpdateResult(
            updated_item=new_item,
            was_updated=True,
            old_score=0,
            new_score=0.8,
            old_tokens=0,
            new_tokens=100
        )

        report = generate_report(dataset, [update], verbosity="normal")

        assert report.total_items == 1
        assert report.num_updated == 1
        assert report.total_tokens == 100

    def test_report_calculates_before_stats(self):
        """Report calculates before-update statistics."""
        items_before = [
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0, tokens=0),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.5, tokens=50),
            EvaluationItem(prompt="Q3", golden_answer="A3", score=0.6, tokens=60),
        ]
        dataset = EvaluationDataset(items=items_before)

        update1 = UpdateResult(
            updated_item=EvaluationItem(prompt="Q1", golden_answer="A1", score=0.7, tokens=100),
            was_updated=True,
            old_score=0,
            new_score=0.7,
            old_tokens=0,
            new_tokens=100
        )

        report = generate_report(dataset, [update1], verbosity="normal")

        # Before stats from original dataset
        # Scores: 0, 0.5, 0.6
        assert report.before_avg_score == pytest.approx((0 + 0.5 + 0.6) / 3, abs=0.01)
        assert report.before_min_score == 0
        assert report.before_max_score == 0.6

    def test_report_calculates_after_stats(self):
        """Report calculates after-update statistics."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.7, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.5, tokens=50),
            EvaluationItem(prompt="Q3", golden_answer="A3", score=0.6, tokens=60),
        ])

        # No updates for this test - after should be the dataset scores
        report = generate_report(dataset, [], verbosity="normal")

        assert report.after_avg_score == pytest.approx((0.7 + 0.5 + 0.6) / 3, abs=0.01)
        assert report.after_min_score == 0.5
        assert report.after_max_score == 0.7

    def test_report_with_multiple_updates(self):
        """Report aggregates multiple updates."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.9, tokens=200),
        ])

        updates = [
            UpdateResult(
                updated_item=EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
                was_updated=True,
                old_score=0,
                new_score=0.8,
                old_tokens=0,
                new_tokens=100
            ),
            UpdateResult(
                updated_item=EvaluationItem(prompt="Q2", golden_answer="A2", score=0.9, tokens=200),
                was_updated=True,
                old_score=0,
                new_score=0.9,
                old_tokens=0,
                new_tokens=200
            ),
        ]

        report = generate_report(dataset, updates, verbosity="normal")

        assert report.total_items == 2
        assert report.num_updated == 2
        assert report.total_tokens == 300

    def test_report_identifies_improvements(self):
        """Report identifies items with score improvements."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
        ])

        update = UpdateResult(
            updated_item=EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
            was_updated=True,
            old_score=0.3,
            new_score=0.8,
            old_tokens=50,
            new_tokens=100
        )

        report = generate_report(dataset, [update], verbosity="normal")

        assert len(report.improvements) == 1
        assert report.improvements[0]["old_score"] == 0.3
        assert report.improvements[0]["new_score"] == 0.8

    def test_report_format_quiet(self):
        """Quiet verbosity produces minimal output."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
        ])

        report = generate_report(dataset, [], verbosity="quiet")

        # Quiet mode should have very little output
        output = report.format()
        assert isinstance(output, str)

    def test_report_format_normal(self):
        """Normal verbosity includes summary."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.8, tokens=150),
        ])

        report = generate_report(dataset, [], verbosity="normal")
        output = report.format()

        # Normal should include counts
        assert "2" in output or "items" in output.lower()

    def test_report_format_verbose(self):
        """Verbose verbosity includes detailed info."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
        ])

        update = UpdateResult(
            updated_item=EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=150),
            was_updated=True,
            old_score=0.5,
            new_score=0.8,
            old_tokens=100,
            new_tokens=150
        )

        report = generate_report(dataset, [update], verbosity="verbose")
        output = report.format()

        # Verbose should include improvements
        assert isinstance(output, str)
        assert len(output) > 0

    def test_report_format_debug(self):
        """Debug verbosity includes most detail."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
        ])

        report = generate_report(dataset, [], verbosity="debug")
        output = report.format()

        assert isinstance(output, str)

    def test_report_stores_improvements(self):
        """Report stores improvement details."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Question 1", golden_answer="Answer 1", score=0.7, tokens=100),
        ])

        update = UpdateResult(
            updated_item=EvaluationItem(prompt="Question 1", golden_answer="Answer 1", score=0.7, tokens=100),
            was_updated=True,
            old_score=0,
            new_score=0.7,
            old_tokens=0,
            new_tokens=100
        )

        report = generate_report(dataset, [update], verbosity="normal")

        assert len(report.improvements) == 1
        imp = report.improvements[0]
        assert "prompt" in imp
        assert "old_score" in imp
        assert "new_score" in imp

    def test_report_handles_no_improvements(self):
        """Report handles case with no improvements."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.5, tokens=100),
        ])

        # No updates
        report = generate_report(dataset, [], verbosity="normal")

        assert report.improvements == []

    def test_report_token_summary(self):
        """Report includes total token summary."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
            EvaluationItem(prompt="Q2", golden_answer="A2", score=0.9, tokens=200),
        ])

        update = UpdateResult(
            updated_item=EvaluationItem(prompt="Q1", golden_answer="A1", score=0.8, tokens=100),
            was_updated=True,
            old_score=0,
            new_score=0.8,
            old_tokens=0,
            new_tokens=100
        )

        report = generate_report(dataset, [update], verbosity="normal")

        assert report.total_tokens == 100  # Only from updates


class TestReportDataStructure:
    """Test Report data structure."""

    def test_report_has_all_fields(self):
        """Report has all expected fields."""
        dataset = EvaluationDataset(items=[
            EvaluationItem(prompt="Q", golden_answer="A", score=0.5, tokens=100),
        ])

        report = generate_report(dataset, [], verbosity="normal")

        assert hasattr(report, 'total_items')
        assert hasattr(report, 'num_updated')
        assert hasattr(report, 'before_avg_score')
        assert hasattr(report, 'before_min_score')
        assert hasattr(report, 'before_max_score')
        assert hasattr(report, 'after_avg_score')
        assert hasattr(report, 'after_min_score')
        assert hasattr(report, 'after_max_score')
        assert hasattr(report, 'total_tokens')
        assert hasattr(report, 'improvements')

    def test_report_format_method_exists(self):
        """Report has format method."""
        dataset = EvaluationDataset(items=[])
        report = generate_report(dataset, [], verbosity="normal")
        assert callable(report.format)
