#!/usr/bin/env python
"""CLI entry point for agent skill grader."""
import sys
from typing import List

from grader.config import parse_args, Config, DEFAULT_MODEL
from grader.yaml_loader import load_yaml
from grader.logger import setup_logger
from grader.claude_scorer import score_item, ScoreExtractionError, TokenUsageError
from grader.score_updater import should_update_score, apply_score_update
from grader.yaml_writer import write_yaml
from grader.reporter import generate_report
from grader.validator import ValidationError


def main(argv: List[str] = None) -> int:
    """Main orchestration function.

    Args:
        argv: Command-line arguments (for testing). If None, uses sys.argv[1:].

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    try:
        # Parse arguments
        args = parse_args(argv)

        # Set up logger
        logger = setup_logger("grader", verbosity=args.verbosity)

        # Validate configuration
        config = Config(path=args.path, model=args.model, verbosity=args.verbosity)
        config.validate()

        logger.info(f"Loading evaluation file: {args.path}")

        # Load YAML
        dataset = load_yaml(args.path)
        logger.info(f"Loaded {len(dataset)} items")

        # Resolve model: CLI arg > YAML field > DEFAULT_MODEL
        yaml_model = dataset.config.model if dataset.config else None
        resolved_model = args.model or yaml_model or DEFAULT_MODEL

        logger.debug(f"Using model: {resolved_model}")

        # Score each item
        updated_items = []
        update_results = []

        for index, item in enumerate(dataset):
            logger.debug(f"Scoring item {index+1}/{len(dataset)}: {item.prompt[:50]}...")

            try:
                agent_binary = dataset.config.agent_binary if dataset.config else None
                new_score, new_tokens = score_item(
                    item.prompt,
                    item.golden_answer,
                    model=resolved_model,
                    agent_binary=agent_binary
                )
                logger.debug(f"  Got score: {new_score}, tokens: {new_tokens}")

                # Decide whether to update
                if should_update_score(item.score, new_score):
                    update = apply_score_update(item, new_score, new_tokens)
                    updated_items.append(update.updated_item)
                    update_results.append(update)

                    if args.verbosity in ("verbose", "debug"):
                        old_score = item.score
                        logger.info(
                            f"Updated item {index}: {old_score:.2f} → {new_score:.2f}"
                        )
                else:
                    # Keep original item
                    updated_items.append(item)
                    logger.debug(f"No update: {item.score} >= {new_score}")

            except (ScoreExtractionError, TokenUsageError) as e:
                logger.critical(f"Error scoring item {index}: {e}")
                return 1
            except Exception as e:
                logger.critical(f"Unexpected error scoring item {index}: {e}")
                return 1

        # Write updated YAML
        logger.info(f"Writing updated file: {args.path}")
        write_yaml(args.path, dataset.__class__(items=updated_items))

        # Generate and display report
        report = generate_report(
            dataset.__class__(items=updated_items),
            update_results,
            verbosity=args.verbosity
        )

        if args.verbosity != "quiet":
            print(report.format())

        return 0

    except FileNotFoundError as e:
        logger = setup_logger("grader", verbosity="quiet")
        logger.critical(f"File not found: {e}")
        return 1
    except ValidationError as e:
        logger = setup_logger("grader", verbosity="quiet")
        logger.critical(f"Validation error: {e}")
        return 1
    except ValueError as e:
        logger = setup_logger("grader", verbosity="quiet")
        logger.critical(f"Invalid input: {e}")
        return 1
    except Exception as e:
        logger = setup_logger("grader", verbosity="quiet")
        logger.critical(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
