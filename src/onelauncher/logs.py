import logging
import sys
from functools import partial
from logging.handlers import RotatingFileHandler
from platform import platform
from types import TracebackType

from .__about__ import __title__, __version__, version_parsed
from .config import platform_dirs

LOGS_DIR = platform_dirs.user_log_path
MAIN_LOG_FILE_NAME = "main.log"


def log_basic_info(logger: logging.Logger) -> None:
    logger.info("Logging started")
    logger.info(f"{__title__}: {__version__}")
    logger.info(platform())


def handle_uncaught_exceptions(
    logger: logging.Logger,
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    """Handler for uncaught exceptions that will write to the logs"""
    if issubclass(exc_type, KeyboardInterrupt):
        # call the default excepthook saved at __excepthook__
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logger.critical(
        "Uncaught exception:", exc_info=(exc_type, exc_value, exc_traceback)
    )


def setup_application_logging() -> None:
    """Create root logger configured for running application"""
    if version_parsed.is_devrelease:
        file_logging_level = logging.DEBUG
        stream_logging_level = logging.DEBUG
    elif version_parsed.is_prerelease:
        file_logging_level = logging.DEBUG
        stream_logging_level = logging.WARNING
    else:
        file_logging_level = logging.INFO
        stream_logging_level = logging.WARNING

    # Make sure logs dir exists
    LOGS_DIR.mkdir(exist_ok=True, parents=True)

    # Create or get custom logger
    logger = logging.getLogger()

    # This is for the logger globally. Different handlers
    # attached to it have their own levels.
    logger.setLevel(logging.DEBUG)

    # Create handlers
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(stream_logging_level)

    log_file = LOGS_DIR / MAIN_LOG_FILE_NAME
    file_handler = RotatingFileHandler(
        filename=log_file,
        mode="a",
        maxBytes=10 * 1024 * 1024,
        backupCount=2,
        encoding=None,
    )
    file_handler.setLevel(file_logging_level)

    # Create formatters and add it to handlers
    stream_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    stream_handler.setFormatter(stream_format)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(lineno)d - %(message)s"
    )
    file_handler.setFormatter(file_format)

    # Add handlers to the logger
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)

    # Setup handling of uncaught exceptions
    sys.excepthook = partial(handle_uncaught_exceptions, logger=logger)

    log_basic_info(logger=logger)
