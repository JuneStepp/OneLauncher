# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'error_message.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QPlainTextEdit, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_errorMessageWindow(object):
    def setupUi(self, errorMessageWindow: QDialog) -> None:
        if not errorMessageWindow.objectName():
            errorMessageWindow.setObjectName(u"errorMessageWindow")
        errorMessageWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        errorMessageWindow.resize(400, 300)
        errorMessageWindow.setModal(True)
        self.verticalLayout = QVBoxLayout(errorMessageWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.textLabel = QLabel(errorMessageWindow)
        self.textLabel.setObjectName(u"textLabel")

        self.verticalLayout.addWidget(self.textLabel)

        self.detailsTextEdit = QPlainTextEdit(errorMessageWindow)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setUndoRedoEnabled(False)
        self.detailsTextEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.buttonBox = QDialogButtonBox(errorMessageWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(errorMessageWindow)
        self.buttonBox.accepted.connect(errorMessageWindow.accept)
        self.buttonBox.rejected.connect(errorMessageWindow.reject)

        QMetaObject.connectSlotsByName(errorMessageWindow)
    # setupUi

    def retranslateUi(self, errorMessageWindow: QDialog) -> None:
        errorMessageWindow.setWindowTitle(QCoreApplication.translate("errorMessageWindow", u"Error", None))
        self.textLabel.setText(QCoreApplication.translate("errorMessageWindow", u"Error:", None))
    # retranslateUi

