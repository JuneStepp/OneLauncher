from PySide6 import QtWidgets, QtCore

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
