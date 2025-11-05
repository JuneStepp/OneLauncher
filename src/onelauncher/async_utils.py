import logging
from collections.abc import Awaitable, Callable
from functools import partial
from typing import Final

import outcome
import trio
from PySide6 import QtCore, QtWidgets
from typing_extensions import override

from onelauncher.qtapp import get_qapp

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
            strict_exception_groups=True,
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
    trio.run(partial(_scope_entry, entry=entry))
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
