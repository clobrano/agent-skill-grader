"""Logging configuration with verbosity control."""
import logging
from typing import Dict

VERBOSITY_LEVELS: Dict[str, int] = {
    "quiet": logging.CRITICAL,
    "normal": logging.WARNING,
    "verbose": logging.INFO,
    "debug": logging.DEBUG,
}


def setup_logger(name: str, verbosity: str = "normal") -> logging.Logger:
    """Set up logger with specified verbosity level.

    Args:
        name: Logger name.
        verbosity: Verbosity level ('quiet', 'normal', 'verbose', 'debug').
                   Defaults to 'normal'.

    Returns:
        Configured Logger instance.
    """
    logger = logging.getLogger(name)

    # Use specified verbosity or default to normal
    level = VERBOSITY_LEVELS.get(verbosity, logging.WARNING)
    logger.setLevel(level)

    # Only add handler if logger doesn't have one
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
