from PySide6 import QtCore, QtGui, QtWidgets
from qframelesswindow import FramelessDialog, FramelessMainWindow
from typing_extensions import override

from onelauncher.network.game_newsfeed import get_newsfeed_css

from .qtapp import get_qapp
from .qtdesigner.custom_widgets import (
    QDialogWithStylePreview,
    QMainWindowWithStylePreview,
)


class FramelessQDialogWithStylePreview(FramelessDialog, QDialogWithStylePreview): ...


class FramelessQMainWindowWithStylePreview(
    FramelessMainWindow, QMainWindowWithStylePreview
): ...


class GameNewsfeedBrowser(QtWidgets.QTextBrowser):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setOpenExternalLinks(True)
        self.setOpenLinks(True)
        self.html: str | None = None
        get_qapp().styleHints().colorSchemeChanged.connect(self.updateStyling)

    @override
    def setHtml(self, text: str) -> None:
        self.document().setDefaultStyleSheet(get_newsfeed_css())
        self.html = text
        return super().setHtml(text)

    def updateStyling(self) -> None:
        """Update CSS styling"""
        if self.html is not None:
            self.setHtml(self.html)


class NoOddSizesQToolButton(QtWidgets.QToolButton):
    """
    Helps icon only buttons keep their icon better centered.

    Credit to [this](https://stackoverflow.com/a/75229629) answer on stackoverflow by
    musicamante.
    """

    @override
    def sizeHint(self) -> QtCore.QSize:
        hint = super().sizeHint()
        if hint.width() % 2:
            hint.setWidth(hint.width() + 1)
        if hint.height() % 2:
            hint.setHeight(hint.height() + 1)
        return hint


class QResizingPixmapLabel(QtWidgets.QLabel):
    """
    `QLabel` for displaying `QPixmap`s that scales the image, keeping aspect ratio.

    Based on [this](https://stackoverflow.com/a/71436950) answer by iblanco on stackoverflow.
    """

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent)
        self.setMinimumSize(1, 1)
        self.setScaledContents(False)
        self._pixmap: QtGui.QPixmap | None = None

    @override
    def heightForWidth(self, width: int) -> int:
        if self._pixmap is None:
            return self.height()
        else:
            return self._pixmap.height() * width // self._pixmap.width()

    @override
    def setPixmap(self, pixmap: QtGui.QPixmap | QtGui.QImage | str) -> None:
        if not isinstance(pixmap, QtGui.QPixmap):
            self._pixmap = QtGui.QPixmap(pixmap)
        else:
            self._pixmap = pixmap
        super().setPixmap(self._pixmap)

    @override
    def sizeHint(self) -> QtCore.QSize:
        width = self.width()
        return QtCore.QSize(width, self.heightForWidth(width))

    @override
    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        if self._pixmap is not None:
            scaled = self._pixmap.scaled(
                self.size() * self.devicePixelRatioF(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(self.devicePixelRatioF())
            super().setPixmap(scaled)
            self.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)


class FixedWordWrapQLabel(QtWidgets.QLabel):
    """
    `QLabel` that calculates size correctly when word wrapping is enabled.

    The label will still be the same width that it would have been
    initially, but the height will be correct. Works good enough for
    the current specific settings window use case.
    """

    @override
    def minimumSizeHint(self) -> QtCore.QSize:
        bounding_rect = self.fontMetrics().boundingRect(
            QtCore.QRect(QtCore.QPoint(), self.sizeHint()),
            QtCore.Qt.TextFlag.TextWordWrap,
            self.text(),
        )
        return bounding_rect.size()

    # I tried reimplementing `heightForWidth` like was done for `minimumSizeHint`, but
    # that still gave the original QLabel behavior.
    @override
    def hasHeightForWidth(self) -> bool:
        return False
