import logging

from PySide6 import QtCore, QtWidgets

logger = logging.getLogger(__name__)


def show_warning_message(message: str, parent: QtWidgets.QWidget | None) -> None:
    message_box = QtWidgets.QMessageBox(parent)
    message_box.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
    message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
    message_box.setStandardButtons(message_box.StandardButton.Ok)
    message_box.setInformativeText(message)

    message_box.exec()


def show_message_box_details_as_markdown(messageBox: QtWidgets.QMessageBox) -> None:
    """Makes the detailed text of messageBox display in Markdown format"""
    button_box: QtWidgets.QDialogButtonBox = messageBox.findChild(  # type: ignore[assignment]
        QtWidgets.QDialogButtonBox, "qt_msgbox_buttonbox"
    )
    for button in button_box.buttons():
        if (
            messageBox.buttonRole(button) == QtWidgets.QMessageBox.ButtonRole.ActionRole
            and button.text() == "Show Details..."
        ):
            button.click()
            detailed_text_widget: QtWidgets.QTextEdit = messageBox.findChild(  # type: ignore[assignment]
                QtWidgets.QTextEdit
            )
            detailed_text_widget.setMarkdown(messageBox.detailedText())
            button.click()
            return


def log_record_to_rich_text(record: logging.LogRecord) -> str:
    if record.levelno == logging.WARNING:
        return f"<font color='#958e55'>{record.message}</font>"
    elif record.levelno >= logging.ERROR:
        return f'<font color="red">{record.message}</font>'
    else:
        return record.message
