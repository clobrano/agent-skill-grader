"""CLI configuration and argument parsing."""
import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Default model to use if none specified
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


@dataclass
class Config:
    """Configuration from CLI arguments."""

    path: str
    model: Optional[str]
    verbosity: str

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
            PermissionError: If the YAML file is not readable.
        """
        path_obj = Path(self.path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {self.path}")
        if not path_obj.is_file():
            raise FileNotFoundError(f"Not a file: {self.path}")
        if not path_obj.stat().st_mode & 0o400:
            raise PermissionError(f"File not readable: {self.path}")


def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: List of command-line arguments (for testing).
              If None, uses sys.argv.

    Returns:
        Parsed arguments as Namespace.
    """
    parser = argparse.ArgumentParser(
        description="Score evaluation items using Claude API"
    )
    parser.add_argument(
        "path",
        help="Path to YAML file containing evaluation items"
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Claude model to use (default: {DEFAULT_MODEL} or YAML model field)"
    )
    parser.add_argument(
        "--verbosity",
        choices=["quiet", "normal", "verbose", "debug"],
        default="normal",
        help="Verbosity level (default: normal)"
    )

    return parser.parse_args(args)
