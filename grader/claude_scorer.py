"""Anthropic SDK integration for scoring evaluation items."""
import json
import re
import subprocess
from typing import Optional, Tuple

from anthropic import Anthropic

# Initialize client (will use ANTHROPIC_API_KEY env var)
client = Anthropic()


class ScoreExtractionError(Exception):
    """Raised when score cannot be extracted from Claude response."""
    pass


class TokenUsageError(Exception):
    """Raised when token usage is missing from response."""
    pass


GRADING_PROMPT_TEMPLATE = """You are an expert evaluator. Compare the golden answer to the actual response and provide a numerical score.

OUTPUT FORMAT (you must follow this exactly):
End your response with a line containing only: Score: X.XX
Where X.XX is a decimal between 0 and 1 (e.g., "Score: 0.85")
Nothing should appear after the score line.

EVALUATION TASK:
Prompt: {prompt}

Golden Answer: {golden_answer}

Evaluate the accuracy and completeness of the response. Consider:
- Factual correctness of all key points
- Completeness (are all important details present?)
- Format alignment (does the output match the expected structure/format?)
- Usefulness (is the output in the right form for the intended use?)

Use this scale:
- 0 = completely wrong, missing, or completely misformatted
- 0.25 = mostly wrong or significant missing content
- 0.5 = partially correct or partially complete
- 0.75 = mostly correct with minor issues
- 1 = completely correct and complete"""


def score_with_agent_binary(agent_path: str, prompt: str) -> Tuple[float, int]:
    """Score an evaluation item using a custom agent binary.

    Args:
        agent_path: Path to the agent binary.
        prompt: The formatted evaluation prompt (already includes prompt and golden_answer).

    Returns:
        Tuple of (score, tokens_used) where:
        - score is 0-1
        - tokens_used is always 0 (agent binary doesn't expose metrics)

    Raises:
        FileNotFoundError: If agent binary is not found.
        ScoreExtractionError: If score cannot be extracted or is invalid.
        Exception: If agent binary exits with non-zero code.
    """
    try:
        result = subprocess.run(
            [agent_path],
            input=prompt,
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        raise Exception(f"Agent binary not found at {agent_path}")

    if result.returncode != 0:
        raise Exception(
            f"Agent binary exited with code {result.returncode}: {result.stderr}"
        )

    output = result.stdout.strip()
    score = _parse_agent_binary_output(output)

    return score, 0


def _parse_agent_binary_output(output: str) -> float:
    """Parse score from agent binary output.

    Tries multiple parsing strategies:
    1. JSON with 'score' field
    2. Pattern "Score: X.XX" (case-insensitive)
    3. Plain float number

    Args:
        output: Raw output from agent binary.

    Returns:
        Score value between 0 and 1.

    Raises:
        ScoreExtractionError: If score cannot be extracted or is invalid.
    """
    # Try JSON parsing first (only if it looks like a dict with '{')
    if output.strip().startswith('{'):
        try:
            data = json.loads(output)
            if isinstance(data, dict) and "score" in data:
                score_value = data["score"]
                # Convert string to float if needed
                if isinstance(score_value, str):
                    try:
                        score = float(score_value)
                    except ValueError as e:
                        raise ScoreExtractionError(
                            f"Score field is not a valid number: {score_value}"
                        ) from e
                else:
                    score = float(score_value)
                _validate_score(score)
                return score
            else:
                raise ScoreExtractionError(
                    f"Agent binary returned JSON but missing 'score' field: {output}"
                )
        except json.JSONDecodeError as e:
            raise ScoreExtractionError(
                f"Agent binary returned invalid JSON: {output}"
            ) from e

    # Try pattern matching for "Score: X.XX" in verbose output
    match = re.search(r'Score:\s*([\d.]+)', output, re.IGNORECASE)
    if match:
        try:
            score = float(match.group(1))
            _validate_score(score)
            return score
        except ValueError as e:
            raise ScoreExtractionError(
                f"Score is not a valid number: {match.group(1)}"
            ) from e

    # Fall back to plain float parsing
    try:
        score = float(output.strip())
    except ValueError as e:
        raise ScoreExtractionError(
            f"Agent binary returned invalid score: {output}"
        ) from e

    _validate_score(score)
    return score


def _validate_score(score: float) -> None:
    """Validate that score is in valid range.

    Args:
        score: Score value to validate.

    Raises:
        ScoreExtractionError: If score is outside 0-1 range.
    """
    if score < 0 or score > 1:
        raise ScoreExtractionError(
            f"Score must be between 0 and 1, got {score}"
        )


def score_item(
    prompt: str,
    golden_answer: str,
    model: str = "claude-3-5-sonnet-20241022",
    agent_binary: Optional[str] = None
) -> Tuple[float, int]:
    """Score an evaluation item using Claude or agent binary.

    Args:
        prompt: The evaluation prompt/question.
        golden_answer: The expected/correct answer.
        model: Claude model to use (default: claude-3-5-sonnet-20241022).
        agent_binary: Path to agent binary. If provided, uses subprocess instead of SDK.

    Returns:
        Tuple of (score, tokens_used) where:
        - score is 0-1
        - tokens_used is output tokens (0 if using agent_binary)

    Raises:
        ScoreExtractionError: If score cannot be extracted or is invalid.
        TokenUsageError: If token usage is missing from response (SDK only).
        Exception: If API call or agent binary fails.
    """
    grading_prompt = GRADING_PROMPT_TEMPLATE.format(
        prompt=prompt,
        golden_answer=golden_answer
    )

    # Use agent binary if provided, otherwise use SDK
    if agent_binary:
        return score_with_agent_binary(agent_binary, grading_prompt)

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": grading_prompt
            }
        ]
    )

    # Extract token usage
    if not response.usage or not hasattr(response.usage, 'output_tokens'):
        raise TokenUsageError("Response missing token usage information")

    tokens_used = response.usage.output_tokens

    # Extract score from response
    response_text = response.content[0].text
    score = _extract_score(response_text)

    return score, tokens_used


def _extract_score(response_text: str) -> float:
    """Extract numerical score from Claude response.

    Args:
        response_text: Text from Claude response.

    Returns:
        Score value between 0 and 1.

    Raises:
        ScoreExtractionError: If score cannot be extracted or is invalid.
    """
    # Look for pattern "Score: X.XX" or "Score: X"
    match = re.search(r'Score:\s*([\d.]+)', response_text, re.IGNORECASE)

    if not match:
        raise ScoreExtractionError(
            f"Could not extract score from response. "
            f"Expected format: 'Score: 0.XX'. "
            f"Response: {response_text[:200]}"
        )

    try:
        score = float(match.group(1))
    except ValueError as e:
        raise ScoreExtractionError(
            f"Score is not a valid number: {match.group(1)}"
        ) from e

    if score < 0 or score > 1:
        raise ScoreExtractionError(
            f"Score must be between 0 and 1, got {score}"
        )

    return score
