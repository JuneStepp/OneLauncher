from PySide6 import QtWidgets, QtCore

def raise_warning_message(message, parent):
    messageBox = QtWidgets.QMessageBox(parent)
    messageBox.setWindowFlag(QtCore.Qt.FramelessWindowHint)
    messageBox.setIcon(QtWidgets.QMessageBox.Warning)
    messageBox.setStandardButtons(messageBox.Ok)
    messageBox.setInformativeText(message)

    messageBox.exec()

def show_message_box_details_as_markdown(messageBox: QtWidgets.QMessageBox):
    """Makes the detailed text of messageBox display in Markdown format"""
    button_box = messageBox.findChild(
        QtWidgets.QDialogButtonBox, "qt_msgbox_buttonbox"
    )
    for button in button_box.buttons():
        if (
            messageBox.buttonRole(
                button) == QtWidgets.QMessageBox.ActionRole
            and button.text() == "Show Details..."
        ):
            button.click()
            detailed_text_widget = messageBox.findChild(
                QtWidgets.QTextEdit)
            detailed_text_widget.setMarkdown(messageBox.detailedText())
            button.click()
            return