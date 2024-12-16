from __future__ import annotations

import logging
import os
import tempfile
from datetime import datetime
from logging import CRITICAL, DEBUG, ERROR, INFO, WARNING, FileHandler, StreamHandler
from pathlib import Path

from uglyrag.logger import configure_basic_logging, configure_file_logging, configure_logger, create_formatter


def test_configure_logger_level():
    logger = StreamHandler()
    configure_logger(logger, "DEBUG")
    assert logger.level == DEBUG

    configure_logger(logger, "INFO")
    assert logger.level == INFO

    configure_logger(logger, "WARNING")
    assert logger.level == WARNING

    configure_logger(logger, "ERROR")
    assert logger.level == ERROR

    configure_logger(logger, "CRITICAL")
    assert logger.level == CRITICAL

    configure_logger(logger, "INVALID_LEVEL")
    assert logger.level == INFO


def test_create_formatter():
    formatter = create_formatter()
    log_record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg="test message", args=(), exc_info=None
    )
    formatted_message = formatter.format(log_record)
    assert " - [INFO] - test message" in formatted_message


def test_configure_basic_logging():
    configure_basic_logging()
    logger = logging.getLogger()
    assert logger.level == DEBUG
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], StreamHandler)
    assert logger.handlers[0].level == INFO
    log_record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0, msg="test message", args=(), exc_info=None
    )
    assert logger.handlers[0].formatter is not None
    formatted_message = logger.handlers[0].formatter.format(log_record)
    assert " - [INFO] - test message" in formatted_message


def test_configure_file_logging():
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)
        configure_file_logging(data_dir, "DEBUG")
        logger = logging.getLogger()
        assert logger.handlers[0].level == DEBUG
        assert logger.handlers[1].level == DEBUG
        assert logger.handlers[0].formatter is not None
        assert logger.handlers[1].formatter is not None
        assert logger.handlers[0].formatter._style._fmt == "%(asctime)s - [%(levelname)s] - %(message)s"
        assert logger.handlers[1].formatter._style._fmt == "%(asctime)s - [%(levelname)s] - %(message)s"
        log_file = data_dir / "logs" / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        assert log_file.exists()
