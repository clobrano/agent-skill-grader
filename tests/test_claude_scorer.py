"""Tests for Claude API scoring."""
import json
import subprocess

import pytest
from unittest.mock import Mock, patch, MagicMock

from grader.claude_scorer import score_item, ScoreExtractionError, TokenUsageError


class TestScoreExtraction:
    """Test score extraction from Claude responses."""

    def test_extract_score_from_valid_response(self):
        """Score is extracted from valid Claude response."""
        mock_response = Mock()
        mock_response.content = [Mock(text="The response is accurate and complete. Score: 0.85")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item("What is 2+2?", "4", model="claude-3-5-sonnet-20241022")
            assert score == 0.85
            assert tokens == 50  # output tokens only

    def test_extract_score_zero(self):
        """Score of 0 is extracted correctly."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Completely wrong. Score: 0")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item("Q", "A", model="claude-3-5-sonnet-20241022")
            assert score == 0

    def test_extract_score_one(self):
        """Score of 1 is extracted correctly."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Perfect answer. Score: 1")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item("Q", "A", model="claude-3-5-sonnet-20241022")
            assert score == 1

    def test_extract_score_decimal(self):
        """Decimal scores are extracted correctly."""
        test_cases = [0.1, 0.25, 0.5, 0.75, 0.99]
        for expected_score in test_cases:
            mock_response = Mock()
            mock_response.content = [Mock(text=f"Score: {expected_score}")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)

            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.return_value = mock_response

                score, tokens = score_item("Q", "A", model="claude-3-5-sonnet-20241022")
                assert score == expected_score

    def test_missing_score_in_response_raises_error(self):
        """Missing score in response raises ScoreExtractionError."""
        mock_response = Mock()
        mock_response.content = [Mock(text="This response has no score")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            with pytest.raises(ScoreExtractionError):
                score_item("Q", "A", model="claude-3-5-sonnet-20241022")

    def test_malformed_score_raises_error(self):
        """Malformed score raises ScoreExtractionError."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: not_a_number")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            with pytest.raises(ScoreExtractionError):
                score_item("Q", "A", model="claude-3-5-sonnet-20241022")

    def test_score_out_of_range_raises_error(self):
        """Score outside 0-1 range raises ScoreExtractionError."""
        test_cases = [-0.1, 1.5, 2, 100]
        for invalid_score in test_cases:
            mock_response = Mock()
            mock_response.content = [Mock(text=f"Score: {invalid_score}")]
            mock_response.usage = Mock(input_tokens=100, output_tokens=50)

            with patch('grader.claude_scorer.client') as mock_client:
                mock_client.messages.create.return_value = mock_response

                with pytest.raises(ScoreExtractionError):
                    score_item("Q", "A", model="claude-3-5-sonnet-20241022")

    def test_missing_token_usage_raises_error(self):
        """Missing token usage raises TokenUsageError."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.5")]
        mock_response.usage = None  # Missing usage

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            with pytest.raises(TokenUsageError):
                score_item("Q", "A", model="claude-3-5-sonnet-20241022")

    def test_token_count_returned(self):
        """Token count from response is returned."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.8")]
        mock_response.usage = Mock(input_tokens=200, output_tokens=75)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item("Q", "A", model="claude-3-5-sonnet-20241022")
            assert tokens == 75  # output tokens

    def test_score_with_whitespace(self):
        """Score with surrounding whitespace is extracted."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Some text\nScore:   0.65   \nMore text")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item("Q", "A", model="claude-3-5-sonnet-20241022")
            assert score == 0.65


class TestScorerIntegration:
    """Test scorer with different models."""

    def test_score_item_accepts_custom_model(self):
        """score_item accepts custom model parameter."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.5")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score_item("Q", "A", model="claude-3-opus-20250729")
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-3-opus-20250729"

    def test_score_item_uses_default_model(self):
        """score_item uses default model if not specified."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.5")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score_item("Q", "A")
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs["model"] == "claude-3-5-sonnet-20241022"

    def test_score_item_sends_prompt_in_messages(self):
        """score_item sends prompt and golden_answer to Claude."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.5")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            prompt = "What is 2+2?"
            golden = "4"
            score_item(prompt, golden, model="claude-3-5-sonnet-20241022")

            call_kwargs = mock_client.messages.create.call_args[1]
            messages = call_kwargs["messages"]
            assert len(messages) > 0
            # Check that prompt and golden answer are in the message
            full_text = str(messages)
            assert prompt in full_text or "2+2" in full_text
            assert golden in full_text or "4" in full_text

    def test_api_error_propagates(self):
        """API errors propagate up."""
        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.side_effect = Exception("API error")

            with pytest.raises(Exception):
                score_item("Q", "A", model="claude-3-5-sonnet-20241022")


class TestAgentBinaryScoring:
    """Test scoring via agent binary subprocess."""

    def test_score_with_agent_binary_plain_number(self):
        """Agent binary output as plain number is parsed correctly."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="0.85",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "test prompt")

            assert score == 0.85
            assert tokens == 0

    def test_score_with_agent_binary_json_output(self):
        """Agent binary output as JSON with score field is parsed."""
        json_output = json.dumps({"score": 0.72, "metadata": "some info"})
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json_output,
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 0.72
            assert tokens == 0

    def test_score_with_agent_binary_json_float_as_string(self):
        """Agent binary JSON with score as string is converted to float."""
        json_output = json.dumps({"score": "0.45"})
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json_output,
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 0.45
            assert tokens == 0

    def test_score_with_agent_binary_zero(self):
        """Agent binary returning 0 is parsed correctly."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="0",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 0.0
            assert tokens == 0

    def test_score_with_agent_binary_one(self):
        """Agent binary returning 1 is parsed correctly."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="1",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 1.0
            assert tokens == 0

    def test_score_with_agent_binary_whitespace_trimmed(self):
        """Agent binary output with whitespace is trimmed."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="  0.33  \n",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 0.33

    def test_score_with_agent_binary_invalid_json_fallback_to_float(self):
        """Invalid JSON in agent output falls back to float parsing."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="0.67",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert score == 0.67

    def test_score_with_agent_binary_out_of_range_raises_error(self):
        """Agent binary returning out-of-range score raises error."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="1.5",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            with pytest.raises(ScoreExtractionError):
                score_with_agent_binary("/path/to/agent", "prompt")

    def test_score_with_agent_binary_invalid_number_raises_error(self):
        """Agent binary returning invalid number raises error."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="not_a_number",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            with pytest.raises(ScoreExtractionError):
                score_with_agent_binary("/path/to/agent", "prompt")

    def test_score_with_agent_binary_json_missing_score_field(self):
        """JSON output without score field raises error."""
        json_output = json.dumps({"result": 0.5, "other": "data"})
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout=json_output,
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            with pytest.raises(ScoreExtractionError):
                score_with_agent_binary("/path/to/agent", "prompt")

    def test_score_with_agent_binary_nonzero_exit_code_raises_error(self):
        """Agent binary exiting with non-zero code raises error."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Error running agent"
            )

            from grader.claude_scorer import score_with_agent_binary
            with pytest.raises(Exception) as exc_info:
                score_with_agent_binary("/path/to/agent", "prompt")
            assert "Agent binary exited with code 1" in str(exc_info.value)

    def test_score_with_agent_binary_file_not_found_raises_error(self):
        """Agent binary not found raises clear error."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("[Errno 2] No such file")

            from grader.claude_scorer import score_with_agent_binary
            with pytest.raises(Exception) as exc_info:
                score_with_agent_binary("/path/to/nonexistent", "prompt")
            assert "Agent binary not found" in str(exc_info.value)

    def test_score_item_uses_agent_binary_when_config_provided(self):
        """score_item routes to agent binary when agent_binary config is provided."""
        with patch('grader.claude_scorer.score_with_agent_binary') as mock_binary:
            mock_binary.return_value = (0.75, 0)

            score, tokens = score_item(
                "test prompt",
                "golden answer",
                agent_binary="/path/to/agent"
            )

            assert score == 0.75
            assert tokens == 0
            # Verify mock was called with correct agent path and a formatted prompt
            assert mock_binary.call_count == 1
            call_args = mock_binary.call_args[0]
            assert call_args[0] == "/path/to/agent"
            # Second arg is the formatted prompt containing test prompt and golden answer
            assert "test prompt" in call_args[1]
            assert "golden answer" in call_args[1]

    def test_score_item_uses_sdk_when_no_agent_binary(self):
        """score_item uses Anthropic SDK when agent_binary is None."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.9")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=50)

        with patch('grader.claude_scorer.client') as mock_client:
            with patch('grader.claude_scorer.score_with_agent_binary') as mock_binary:
                mock_client.messages.create.return_value = mock_response

                score, tokens = score_item(
                    "test prompt",
                    "golden answer",
                    agent_binary=None
                )

                assert score == 0.9
                assert tokens == 50
                mock_binary.assert_not_called()

    def test_score_item_agent_binary_passes_prompt_to_subprocess(self):
        """Agent binary receives formatted prompt via subprocess."""
        from grader.models import EvaluationConfig

        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="0.5",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            prompt_text = "What is 2+2?"
            score_with_agent_binary("/path/to/agent", prompt_text)

            # Verify subprocess was called with correct arguments
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[0][0] == ["/path/to/agent"]
            assert call_args[1]["input"] == prompt_text
            assert call_args[1]["capture_output"] is True
            assert call_args[1]["text"] is True

    def test_score_item_tokens_zero_when_using_agent_binary(self):
        """score_item returns tokens=0 when using agent binary."""
        with patch('grader.claude_scorer.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="0.88",
                stderr=""
            )

            from grader.claude_scorer import score_with_agent_binary
            score, tokens = score_with_agent_binary("/path/to/agent", "prompt")

            assert tokens == 0
            assert score == 0.88

    def test_score_item_tokens_present_when_using_sdk(self):
        """score_item returns actual token count when using SDK."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Score: 0.7")]
        mock_response.usage = Mock(input_tokens=100, output_tokens=35)

        with patch('grader.claude_scorer.client') as mock_client:
            mock_client.messages.create.return_value = mock_response

            score, tokens = score_item(
                "test prompt",
                "golden answer",
                agent_binary=None
            )

            assert tokens == 35
            assert tokens > 0
