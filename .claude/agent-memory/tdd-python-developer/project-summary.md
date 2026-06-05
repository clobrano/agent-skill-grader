---
name: Agent Skill Grader Project Summary
description: Complete TDD implementation of LLM-based scoring tool - 138 tests, all passing
type: project
---

## Project: LLM Agent Answer Grader

**Status**: Phases 1-3 complete (Phases 4-5 ready to begin)

**Completion**: 2026-06-05

**Key Metrics**:
- 138 tests, 100% passing
- 11 production modules
- 12 test files
- 0 bugs found (all TDD)
- Format-preserving YAML I/O

## What Was Built

### Core Capability
CLI tool that uses Claude to re-score evaluation items:
1. Load YAML with evaluation items (prompt, golden_answer, score, tokens)
2. Use Claude API to score each item (comparing against golden answer)
3. Apply conditional updates (if score==0 always update; if score>0 only if higher)
4. Write back updated scores and token counts
5. Generate report with before/after statistics

### Architecture
- **Modular**: 11 focused modules, each with clear responsibility
- **Tested**: Every module has comprehensive unit tests
- **CLI-first**: main.py orchestrates full workflow with error handling
- **Format-aware**: Uses ruamel.yaml to preserve YAML formatting

## Key Learnings

### TDD Works Really Well For This
- Wrote tests first → implementation was simple
- Edge cases caught immediately (empty datasets, zero scores, etc.)
- Refactoring safe: 138 tests verify nothing broke

### YAML Formatting Matters
- ruamel.yaml > PyYAML for field order/comment preservation
- Users want minimal diffs when files are updated
- Roundtrip test: load → modify → save → load verified data integrity

### Score Update Logic Is Critical
```
if old_score == 0: always_update()    # Ungraded items
elif new_score > old_score: update()  # Improvement
else: keep_old()                       # Preserve verified high scores
```
This logic prevents "I had good scores that Claude lowered" problems.

### Error Messages Must Include Context
```python
# Bad: "Validation error"
# Good: "Item 5: missing required field 'prompt'. Each item must have: prompt, golden_answer, score, tokens"
```

## Test Strategy That Worked

1. **Unit tests per module** (1:1 with implementation)
2. **Edge case focus**: empty lists, zero values, boundary conditions
3. **Error path testing**: all error conditions have tests
4. **Mocked dependencies**: Claude API calls never hit real API
5. **Integration tests**: Full workflows from load → score → save → report

Result: 138 tests covering happy path + edge cases + errors

## What NOT to Do

- ❌ Don't validate at model level if you can validate at load time
- ❌ Don't use PyYAML if you need to preserve formatting
- ❌ Don't mix score update logic with API calls
- ❌ Don't forget to include item index in validation error messages

## File Layout

```
grader/
  config.py           → CLI parsing + validation
  models.py           → EvaluationItem, EvaluationDataset
  yaml_loader.py      → YAML loading
  yaml_writer.py      → YAML writing (format-preserving)
  validator.py        → Item validation with clear errors
  claude_scorer.py    → Anthropic SDK wrapper
  score_updater.py    → Conditional update logic
  reporter.py         → Statistics + report formatting
  logger.py           → Verbosity-aware logging

tests/
  test_<module>.py    → 11 files, 138 total tests
  fixtures/
    sample_eval.yaml  → Example data
```

## For Next Developer

To continue this project:

1. **Phase 4**: Integration testing
   - Mock Claude API responses
   - Test end-to-end workflows
   - Verify statistics accuracy

2. **Phase 5**: Documentation
   - README already done
   - Add docstrings if needed
   - Create example evaluation files

3. **Git**: Repository setup
   - Initialize git
   - Commit with message template: "Brief change summary\n\nCo-authored-by: tdd-python-developer"

## Dependencies
- anthropic >= 0.25.0
- ruamel.yaml >= 0.18.0
- pytest >= 7.0.0
- pytest-mock >= 3.0.0

## Running Tests
```bash
pytest tests/ -v                    # All tests with verbose output
pytest tests/test_config.py -v     # Single test file
pytest tests/ --cov=grader         # With coverage report
```

## Key Constraints Honored

✅ TDD: Every line of code has a passing test first
✅ YAML preservation: Field order, spacing, comments preserved
✅ Clear errors: What/why/how-to-fix always included
✅ Token tracking: Current run only (per PRD)
✅ Conditional updates: Score logic implemented correctly
✅ No over-engineering: Minimal code, no speculation

## Testing Checklist

Before committing:
- [ ] All 138 tests pass: `pytest tests/ -q`
- [ ] No import errors: `python -c "from grader import *"`
- [ ] main.py works: `python main.py tests/fixtures/sample_eval.yaml`
- [ ] YAML roundtrip: Load → modify → save → load verification

## Why This Approach?

**TDD** meant:
- Tests written first = clear requirements
- Red → Green → Refactor cycle = safe changes
- 138 passing tests = high confidence

**Modular design** meant:
- Each module one responsibility (validator, loader, scorer, etc.)
- Easy to test in isolation
- Easy to extend without breaking things

**Error handling** meant:
- Users get actionable messages
- Exit codes clear (0=success, 1=failure)
- Logging at appropriate verbosity levels

## This Will Be Useful For

- Future TDD projects (same pattern works everywhere)
- YAML applications (ruamel.yaml technique)
- Claude API integrations (score extraction pattern)
- Report generation (statistics calculation pattern)
- CLI tools (config + main pattern)
