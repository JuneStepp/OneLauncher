import logging
import os
import sys
from collections.abc import Callable
from enum import IntEnum
from functools import partial
from logging.handlers import RotatingFileHandler
from pathlib import Path
from platform import platform
from types import TracebackType
from typing import Final

from typing_extensions import override

from onelauncher.async_utils import app_cancel_scope
from onelauncher.resources import data_dir

from .__about__ import __title__, __version__, version_parsed
from .config import platform_dirs

LOGS_DIR = platform_dirs.user_log_path
MAIN_LOG_FILE_NAME = "main.log"


class LogLevel(IntEnum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


def log_basic_info(logger: logging.Logger) -> None:
    logger.info("Logging started")
    logger.info("%s: %s", __title__, __version__)
    logger.info(platform())
    logger.info("Data Dir: %s", data_dir)


def handle_uncaught_exceptions(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
    logger: logging.Logger,
) -> None:
    """Handler for uncaught exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    app_cancel_scope.cancel()


class RedactHomeDirFormatter(logging.Formatter):
    """
    Redact home directory from log messages. It often contains sensitive
    information like the users's name.
    """

    @override
    def format(self, record: logging.LogRecord) -> str:
        unredacted = super().format(record)
        return unredacted.replace(str(Path.home()), "<HOME>")


def setup_application_logging(log_level_override: LogLevel | None = None) -> None:
    """Create root logger configured for running application"""
    if log_level_override is not None:
        file_logging_level = log_level_override
        stream_logging_level = log_level_override
    elif version_parsed.is_devrelease:
        file_logging_level = LogLevel.DEBUG
        stream_logging_level = LogLevel.INFO
    elif version_parsed.is_prerelease:
        file_logging_level = LogLevel.DEBUG
        stream_logging_level = LogLevel.WARNING
    else:
        file_logging_level = LogLevel.INFO
        stream_logging_level = LogLevel.WARNING

    LOGS_DIR.mkdir(exist_ok=True, parents=True)

    # Create or get custom logger.
    logger = logging.getLogger()
    logging.logThreads = False

    # This is for the logger globally. Different handlers
    # attached to it have their own levels.
    logger.setLevel(LogLevel.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_logging_level)
    stream_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_format)
    logger.addHandler(stream_handler)

    # Don't log to file during testing.
    if os.environ.get("PYTEST_VERSION") is None:
        log_file = LOGS_DIR / MAIN_LOG_FILE_NAME
        file_handler = RotatingFileHandler(
            filename=log_file,
            mode="a",
            maxBytes=10 * 1024 * 1024,
            backupCount=2,
            encoding=None,
        )
        file_handler.setLevel(file_logging_level)
        file_format = RedactHomeDirFormatter(
            "%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    # Setup handling of uncaught exceptions
    sys.excepthook = partial(handle_uncaught_exceptions, logger=logger)

    log_basic_info(logger=logger)


class ForwardLogsHandler(logging.Handler):
    """
    Send new log records to `new_log_callback`. Useful for showing log messages in a UI
    """

    def __init__(
        self, new_log_callback: Callable[[logging.LogRecord], None], level: int = 0
    ) -> None:
        super().__init__(level)
        self.new_log_callback = new_log_callback

    @override
    def emit(self, record: logging.LogRecord) -> None:
        self.format(record=record)
        self.new_log_callback(record)


class ExternalProcessLogsFilter(logging.Filter):
    """
    Filter that sets the `LogRecord` process ID to the value for the key
    `EXTERNAL_PROCESS_ID_KEY` in the `extra` logging keyword argument.
    Used when logging output from external processes.
    """

    EXTERNAL_PROCESS_ID_KEY: Final = "externalProcessID"

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, self.EXTERNAL_PROCESS_ID_KEY):
            record.process = getattr(record, self.EXTERNAL_PROCESS_ID_KEY)
        return True
