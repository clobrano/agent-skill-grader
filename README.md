# Agent Skill Grader

An LLM-based evaluation tool that uses Claude to score agent responses against golden answers, with intelligent score update logic and comprehensive reporting.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Invocation

Score an evaluation YAML file with default settings:

```bash
python main.py path/to/evaluation.yaml
```

### With Custom Agent Binary

Use your own agent binary (no API key needed):

```bash
python main.py path/to/evaluation.yaml
```

(Configure `agent_binary: "/path/to/agent"` in the YAML file)

### With Custom Model

Use a different Claude model:

```bash
python main.py path/to/evaluation.yaml --model claude-3-opus-20250729
```

Or configure in YAML:
```yaml
model: "claude-3-opus-20250729"
items:
  - ...
```

CLI `--model` flag overrides YAML config.

### Verbosity Control

Control output verbosity:

```bash
# Quiet: only errors
python main.py path/to/evaluation.yaml --verbosity quiet

# Normal: summary statistics (default)
python main.py path/to/evaluation.yaml --verbosity normal

# Verbose: per-item updates and improvements
python main.py path/to/evaluation.yaml --verbosity verbose

# Debug: all details including prompts and agent responses
python main.py path/to/evaluation.yaml --verbosity debug
```

## YAML Format

Evaluation files must contain a list of items with optional top-level configuration:

```yaml
# Optional: Configure agent and model for all items
agent_binary: "/path/to/agent"  # Optional: use custom agent binary instead of Anthropic API
model: "claude-3-5-sonnet-20241022"  # Optional: Claude model to use (default: Claude 3.5 Sonnet)

items:
  - prompt: "What is the capital of France?"
    golden_answer: "Paris"
    score: 0
    tokens: 0
  - prompt: "What is 2+2?"
    golden_answer: "4"
    score: 0.8
    tokens: 150
```

### Top-Level Configuration

- **agent_binary** (optional): Path to a custom agent binary to use for scoring instead of the Anthropic API
  - When specified, the tool runs: `echo "prompt" | /path/to/agent`
  - Agent binary output can be a plain number (0-1) or JSON with a `score` field
  - Token tracking is disabled when using agent binary (returns 0)
  - If not specified, falls back to Anthropic SDK (requires proper auth)

- **model** (optional): Claude model to use for scoring (e.g., "claude-3-opus-20250729")
  - Default: "claude-3-5-sonnet-20241022"
  - Ignored if `agent_binary` is specified
  - Can be overridden via CLI flag: `--model claude-3-5-sonnet-20241022`

### Item Fields

- **prompt** or **prompt_file**: The evaluation question or prompt
  - `prompt`: Inline string (e.g., `"What is the capital of France?"`)
  - `prompt_file`: Path to file containing the prompt (e.g., `"prompts/q1.txt"`)
  - At least one must be provided; `prompt_file` takes precedence if both exist

- **golden_answer** or **golden_answer_file**: The correct/expected answer
  - `golden_answer`: Inline string (e.g., `"Paris"`)
  - `golden_answer_file`: Path to file containing the answer (e.g., `"answers/a1.txt"`)
  - At least one must be provided; `golden_answer_file` takes precedence if both exist

- **score**: Current score from 0.0 to 1.0 (float)
  - 0: Ungraded item (will be scored by agent/Claude)
  - 0-1: Previously graded (will be updated only if new score is higher)

- **tokens**: Tokens consumed in this evaluation run (integer, 0 for ungraded items)

### Complete Example

```yaml
agent_binary: "/usr/local/bin/my-agent"
model: "claude-3-5-sonnet-20241022"

items:
  # Using custom agent binary with inline content
  - prompt: "What is the capital of France?"
    golden_answer: "Paris"
    score: 0
    tokens: 0

  # Using file references with agent binary
  - prompt_file: "prompts/question2.txt"
    golden_answer_file: "answers/answer2.txt"
    score: 0
    tokens: 0

  # Mixed: file prompt, inline answer
  - prompt_file: "prompts/question3.txt"
    golden_answer: "The expected answer"
    score: 0.7
    tokens: 200

  # Anthropic API example (no agent_binary means use Anthropic SDK)
  # Simply remove agent_binary field to use Anthropic
```

## Score Update Logic

The tool applies conditional score updates based on the original score:

1. **If score == 0** (ungraded): Always update with Claude's score
2. **If score > 0** (already graded): Update only if Claude's score is higher

This preserves manually-verified high scores while improving ungraded or low-confidence items.

## Output

After processing, the tool:
1. Updates the YAML file in-place with new scores and token counts
2. Displays a summary report with:
   - Total items processed
   - Number of items updated
   - Score statistics (before/after averages, min, max)
   - Total tokens consumed
   - List of improved items (with verbosity=verbose or higher)

### Example Report

```
============================================================
Evaluation Report
============================================================

Total items processed: 3
Items updated: 2
Total tokens used: 350

Score Statistics:
  Before update:
    Average: 0.567
    Min: 0.000
    Max: 0.900
  After update:
    Average: 0.800
    Min: 0.000
    Max: 0.900

Score Improvements:
  What is the capital of France?: 0.00 → 0.95 (+0.95, 150 tokens)
  What is 2+2?: 0.00 → 0.90 (+0.90, 200 tokens)
============================================================
```

## Error Handling

The tool provides clear error messages for common issues:

- **File not found**: Specify the correct path to your YAML file
- **Invalid YAML**: Check the file syntax and structure against the format specification above
- **Invalid scores**: Ensure all scores are between 0.0 and 1.0
- **Missing fields**: Verify all items have prompt, golden_answer, score, and tokens fields
- **API errors**: Check your ANTHROPIC_API_KEY environment variable and network connection

## Authentication & Configuration

### Using Anthropic API (Default)

Requires one of:
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- Google Cloud Vertex AI credentials (if `CLAUDE_CODE_USE_VERTEX` and `ANTHROPIC_VERTEX_PROJECT_ID` are set)

Example:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python main.py evals.yaml
```

### Using Custom Agent Binary

No API key required. Configure in YAML:

```yaml
agent_binary: "/path/to/agent"
items:
  - prompt: "..."
    golden_answer: "..."
    score: 0
    tokens: 0
```

The agent binary is called as:
```bash
echo "prompt text" | /path/to/agent
```

Expected output: A number (0-1) or JSON with a `score` field.

Example agent binary responses:
```
0.85
```

or

```json
{"score": 0.85, "reasoning": "..."}
```

## Testing

Run all tests:

```bash
pytest tests/
```

Run specific test file:

```bash
pytest tests/test_config.py -v
```

Run with coverage:

```bash
pytest tests/ --cov=grader --cov-report=term-missing
```

## Architecture

The tool is organized into modular components:

- **config.py**: CLI argument parsing and validation
- **models.py**: Data models (EvaluationItem, EvaluationDataset)
- **yaml_loader.py**: YAML file loading with validation
- **yaml_writer.py**: YAML file writing with format preservation
- **validator.py**: Item field validation
- **claude_scorer.py**: Anthropic SDK integration
- **score_updater.py**: Conditional score update logic
- **reporter.py**: Report generation and statistics
- **logger.py**: Logging configuration with verbosity control
- **main.py**: CLI orchestration

## Development

Each module includes comprehensive unit tests following TDD principles. Tests are located in `tests/` directory with a test file for each module.

To add a new feature:
1. Write tests in `tests/test_<module>.py`
2. Implement the feature in `grader/<module>.py`
3. Run tests to verify: `pytest tests/test_<module>.py -v`

## License

(Add appropriate license information)

## Support

For issues or questions, please check:
1. The YAML format matches the specification above
2. Your ANTHROPIC_API_KEY is set correctly
3. You have the latest version of dependencies: `pip install -r requirements.txt --upgrade`
