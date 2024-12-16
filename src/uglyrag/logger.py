from __future__ import annotations

import logging
from datetime import datetime
from logging import FileHandler, Formatter, StreamHandler
from pathlib import Path

# 缓存格式化器
formatter: Formatter = Formatter("%(asctime)s - [%(levelname)s] - %(message)s")


def create_formatter() -> Formatter:
    return formatter


def configure_logger(logger: StreamHandler | FileHandler, level_str: str) -> None:
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = levels.get(level_str.upper(), logging.INFO)
    logger.setLevel(log_level)


def configure_basic_logging() -> None:
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    stream_handler = StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(create_formatter())

    logger.addHandler(stream_handler)
    logging.debug("基本日志配置完成")


def configure_file_logging(data_dir: Path, log_level: str, log_file_name: str = "") -> None:
    logs_dir = data_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if not log_file_name:
        log_file_name = f"{datetime.now().strftime('%Y-%m-%d')}.log"
    log_file = logs_dir / log_file_name

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(create_formatter())

    stream_handler = StreamHandler()
    configure_logger(stream_handler, log_level)
    stream_handler.setFormatter(create_formatter())

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    logging.debug(f"日志文件已配置为: {log_file}")
