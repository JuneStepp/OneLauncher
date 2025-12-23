import logging
from collections.abc import Awaitable, Callable
from functools import partial
from tempfile import TemporaryDirectory
from types import TracebackType
from typing import Final

import outcome
import trio
from PySide6 import QtCore, QtWidgets
from trio.abc import ReceiveStream
from typing_extensions import override

from .ui.qtapp import get_qapp

logger = logging.getLogger(__name__)

app_cancel_scope: Final = trio.CancelScope()
"""Top-level cancel scope. Canceling it will exit the program."""


class AsyncHelper(QtCore.QObject):
    class ReenterQtObject(QtCore.QObject):
        """This is a QObject to which an event will be posted, allowing
        Trio to resume when the event is handled. event.fn() is the
        next entry point of the Trio event loop."""

        @override
        def event(self, event: QtCore.QEvent) -> bool:
            if event.type() == QtCore.QEvent.Type.User + 1 and isinstance(
                event, AsyncHelper.ReenterQtEvent
            ):
                event.fn()
                return True
            return False

    class ReenterQtEvent(QtCore.QEvent):
        """This is the QEvent that will be handled by the ReenterQtObject.
        self.fn is the next entry point of the Trio event loop."""

        def __init__(self, fn: Callable[[], object]):
            super().__init__(QtCore.QEvent.Type(QtCore.QEvent.Type.User + 1))
            self.fn = fn

    def __init__(self, entry: Callable[[], Awaitable[object]]):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry

    def launch_guest_run(self) -> None:
        """
        To use Trio and Qt together, one must run the Trio event
        loop as a "guest" inside the Qt "host" event loop.
        """
        trio.lowlevel.start_guest_run(
            self.entry,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
            restrict_keyboard_interrupt_to_checkpoints=True,
        )

    def next_guest_run_schedule(self, fn: Callable[[], object]) -> None:
        """
        This function serves to re-schedule the guest (Trio) event
        loop inside the host (Qt) event loop. It is called by Trio
        at the end of an event loop run in order to relinquish back
        to Qt's event loop. By posting an event on the Qt event loop
        that contains Trio's next entry point, it ensures that Trio's
        event loop will be scheduled again by Qt.
        """
        QtWidgets.QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, run_outcome: outcome.Outcome[object]) -> None:
        """This function is called by Trio when its event loop has
        finished."""
        if isinstance(run_outcome, outcome.Error):
            error = run_outcome.error
            logger.error("Trio Event loop error", exc_info=error)

        if qapp := QtCore.QCoreApplication.instance():
            qapp.exit()


async def _scope_entry(entry: Callable[[], Awaitable[None]]) -> None:
    with app_cancel_scope:
        await entry()


def start_async(entry: Callable[[], Awaitable[None]]) -> int:
    """
    Returns:
        int: Exit code
    """
    trio.run(
        partial(_scope_entry, entry=entry),
        restrict_keyboard_interrupt_to_checkpoints=True,
    )
    return 0


def start_async_gui(entry: Callable[[], Awaitable[None]]) -> int:
    """
    Returns:
        int: Exit code
    """
    qapp = get_qapp()
    async_helper = AsyncHelper(partial(_scope_entry, entry=entry))
    QtCore.QTimer.singleShot(0, async_helper.launch_guest_run)
    # qapp.exec() won't return until trio event loop finishes.
    return qapp.exec()


async def for_each_in_stream(pipe: ReceiveStream, func: Callable[[str], None]) -> None:
    async for chunk in pipe:
        for line in chunk.decode("utf-8").split("\n"):
            if stripped_line := line.strip():
                func(stripped_line)


# Based on `anyio` code.
class TemporaryDirectoryAsyncPath:
    """
    An asynchronous temporary directory that is created and cleaned up automatically.

    This class provides an asynchronous context manager for creating a temporary
    directory. It wraps Python's standard :class:`~tempfile.TemporaryDirectory` to
    perform directory creation and cleanup operations in a background thread, and
    returns it as a `trio.Path`.

    :param suffix: Suffix to be added to the temporary directory name.
    :param prefix: Prefix to be added to the temporary directory name.
    :param dir: The parent directory where the temporary directory is created.
    :param ignore_cleanup_errors: Whether to ignore errors during cleanup
    """

    def __init__(
        self,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,  # noqa: A002
        *,
        ignore_cleanup_errors: bool = False,
    ) -> None:
        self.suffix: str | None = suffix
        self.prefix: str | None = prefix
        self.dir: str | None = dir
        self.ignore_cleanup_errors = ignore_cleanup_errors

        self._tempdir: TemporaryDirectory[str] | None = None

    async def __aenter__(self) -> trio.Path:
        self._tempdir = await trio.to_thread.run_sync(
            partial(
                TemporaryDirectory,
                suffix=self.suffix,
                prefix=self.prefix,
                dir=self.dir,
                ignore_cleanup_errors=self.ignore_cleanup_errors,
            )
        )
        return trio.Path(await trio.to_thread.run_sync(self._tempdir.__enter__))

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._tempdir is not None:
            await trio.to_thread.run_sync(
                self._tempdir.__exit__, exc_type, exc_value, traceback
            )

    async def cleanup(self) -> None:
        if self._tempdir is not None:
            await trio.to_thread.run_sync(self._tempdir.cleanup)
