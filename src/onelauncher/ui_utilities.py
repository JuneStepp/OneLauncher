import logging

import outcome
import trio
from PySide6 import QtCore, QtWidgets


def show_warning_message(message: str, parent: QtWidgets.QWidget):
    messageBox = QtWidgets.QMessageBox(parent)
    messageBox.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
    messageBox.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    messageBox.setStandardButtons(messageBox.StandardButton.Ok)
    messageBox.setInformativeText(message)

    messageBox.exec()


def show_message_box_details_as_markdown(messageBox: QtWidgets.QMessageBox):
    """Makes the detailed text of messageBox display in Markdown format"""
    button_box: QtWidgets.QDialogButtonBox = messageBox.findChild(  # type: ignore
        QtWidgets.QDialogButtonBox, "qt_msgbox_buttonbox"
    )
    for button in button_box.buttons():
        if (
            messageBox.buttonRole(
                button) == QtWidgets.QMessageBox.ButtonRole.ActionRole
            and button.text() == "Show Details..."
        ):
            button.click()
            detailed_text_widget: QtWidgets.QTextEdit = messageBox.findChild(  # type: ignore
                QtWidgets.QTextEdit)
            detailed_text_widget.setMarkdown(messageBox.detailedText())
            button.click()
            return


class AsyncHelper(QtCore.QObject):
    class ReenterQtObject(QtCore.QObject):
        """ This is a QObject to which an event will be posted, allowing
            Trio to resume when the event is handled. event.fn() is the
            next entry point of the Trio event loop. """
        def event(self, event):
            if event.type() == QtCore.QEvent.Type.User + 1:
                event.fn()
                return True
            return False

    class ReenterQtEvent(QtCore.QEvent):
        """ This is the QEvent that will be handled by the ReenterQtObject.
            self.fn is the next entry point of the Trio event loop. """
        def __init__(self, fn):
            super().__init__(QtCore.QEvent.Type(QtCore.QEvent.Type.User + 1))
            self.fn = fn

    def __init__(self, entry):
        super().__init__()
        self.reenter_qt = self.ReenterQtObject()
        self.entry = entry

    @QtCore.Slot()
    def launch_guest_run(self):
        """
        To use Trio and Qt together, one must run the Trio event
        loop as a "guest" inside the Qt "host" event loop.
        """
        if not self.entry:
            raise Exception("No entry point for the Trio guest run was set.")
        trio.lowlevel.start_guest_run(
            self.entry,
            run_sync_soon_threadsafe=self.next_guest_run_schedule,
            done_callback=self.trio_done_callback,
            strict_exception_groups=True
        )

    def next_guest_run_schedule(self, fn):
        """
        This function serves to re-schedule the guest (Trio) event
        loop inside the host (Qt) event loop. It is called by Trio
        at the end of an event loop run in order to relinquish back
        to Qt's event loop. By posting an event on the Qt event loop
        that contains Trio's next entry point, it ensures that Trio's
        event loop will be scheduled again by Qt.
        """
        QtWidgets.QApplication.postEvent(self.reenter_qt, self.ReenterQtEvent(fn))

    def trio_done_callback(self, outcome_):
        """ This function is called by Trio when its event loop has
            finished. """
        if isinstance(outcome_, outcome.Error):
            error = outcome_.error
            logger.error("Trio Event loop error", exc_info=error)

        if qapp := QtCore.QCoreApplication.instance():
            qapp.exit()


logger = logging.getLogger("main")
