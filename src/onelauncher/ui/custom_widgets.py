from PySide6 import QtWidgets
from typing_extensions import override

class QWidgetWithStylePreview(QtWidgets.QWidget):
    """
    QWidget that is used in QtDesigner plugin for stylesheet previewing.
    Acts identical to a normal QWidget during runtime.
    """

class QDialogWithStylePreview(QtWidgets.QDialog):
    """
    QDialog that is used in QtDesigner plugin for stylesheet previewing.
    Acts identical to a normal QDialog during runtime.
    """


class QMainWindowWithStylePreview(QtWidgets.QMainWindow):
    """
    QMainWindow that is used in QtDesigner plugin for stylesheet previewing.
    Acts identical to a normal QMainWindow during runtime.
    """

