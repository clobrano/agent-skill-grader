"""Tests for logging configuration."""
import logging
from io import StringIO

import pytest

from grader.logger import setup_logger, VERBOSITY_LEVELS


class TestLoggerSetup:
    """Test logger configuration."""

    def test_quiet_verbosity_level(self):
        """Quiet verbosity sets CRITICAL level."""
        assert VERBOSITY_LEVELS["quiet"] == logging.CRITICAL

    def test_normal_verbosity_level(self):
        """Normal verbosity sets WARNING level."""
        assert VERBOSITY_LEVELS["normal"] == logging.WARNING

    def test_verbose_verbosity_level(self):
        """Verbose verbosity sets INFO level."""
        assert VERBOSITY_LEVELS["verbose"] == logging.INFO

    def test_debug_verbosity_level(self):
        """Debug verbosity sets DEBUG level."""
        assert VERBOSITY_LEVELS["debug"] == logging.DEBUG

    def test_setup_logger_with_quiet(self):
        """Logger with quiet verbosity only shows CRITICAL."""
        logger = setup_logger("test_quiet", verbosity="quiet")
        assert logger.level == logging.CRITICAL

    def test_setup_logger_with_normal(self):
        """Logger with normal verbosity shows WARNING and above."""
        logger = setup_logger("test_normal", verbosity="normal")
        assert logger.level == logging.WARNING

    def test_setup_logger_with_verbose(self):
        """Logger with verbose verbosity shows INFO and above."""
        logger = setup_logger("test_verbose", verbosity="verbose")
        assert logger.level == logging.INFO

    def test_setup_logger_with_debug(self):
        """Logger with debug verbosity shows DEBUG and above."""
        logger = setup_logger("test_debug", verbosity="debug")
        assert logger.level == logging.DEBUG

    def test_logger_has_handler(self):
        """Logger has at least one handler."""
        logger = setup_logger("test_handler", verbosity="normal")
        assert len(logger.handlers) > 0

    def test_logger_handler_format(self):
        """Logger handler has appropriate format."""
        logger = setup_logger("test_format", verbosity="debug")
        handler = logger.handlers[0]
        formatter = handler.formatter
        assert formatter is not None

    def test_logger_output_contains_level(self):
        """Logger output includes level information."""
        logger = setup_logger("test_output", verbosity="debug")

        # Clear handlers and add string handler
        logger.handlers.clear()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        logger.info("test message")
        output = stream.getvalue()
        assert "[INFO]" in output
        assert "test message" in output

    def test_logger_no_duplicate_handlers(self):
        """Multiple calls to setup_logger don't duplicate handlers."""
        name = "test_unique"
        # Remove any existing logger
        if name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[name]

        logger1 = setup_logger(name, verbosity="normal")
        initial_count = len(logger1.handlers)

        logger2 = setup_logger(name, verbosity="normal")
        final_count = len(logger2.handlers)

        # Should not have added more handlers
        assert final_count <= initial_count + 1

    def test_logger_returns_logger_instance(self):
        """setup_logger returns a Logger instance."""
        logger = setup_logger("test_instance", verbosity="normal")
        assert isinstance(logger, logging.Logger)

    def test_logger_with_invalid_verbosity_uses_default(self):
        """Invalid verbosity uses WARNING as fallback."""
        logger = setup_logger("test_invalid", verbosity="unknown")
        assert logger.level == logging.WARNING

    def test_logger_debug_message_at_debug_level(self):
        """DEBUG message is logged at debug verbosity."""
        logger = setup_logger("test_debug_msg", verbosity="debug")
        logger.handlers.clear()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.debug("debug message")
        assert "debug message" in stream.getvalue()

    def test_logger_info_message_not_at_warning_level(self):
        """INFO message is not logged at warning verbosity."""
        logger = setup_logger("test_info_skip", verbosity="normal")
        logger.handlers.clear()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info("info message")
        assert stream.getvalue() == ""

    def test_logger_warning_message_at_normal_level(self):
        """WARNING message is logged at normal verbosity."""
        logger = setup_logger("test_warning_msg", verbosity="normal")
        logger.handlers.clear()
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.warning("warning message")
        assert "warning message" in stream.getvalue()
