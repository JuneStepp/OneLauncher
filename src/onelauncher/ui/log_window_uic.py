# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'log_window.ui'
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
    QPlainTextEdit, QSizePolicy, QVBoxLayout, QWidget)

class Ui_logDialog(object):
    def setupUi(self, logDialog: QDialog) -> None:
        if not logDialog.objectName():
            logDialog.setObjectName(u"logDialog")
        logDialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        logDialog.resize(400, 300)
        logDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(logDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.detailsTextEdit = QPlainTextEdit(logDialog)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setUndoRedoEnabled(False)
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.buttonBox = QDialogButtonBox(logDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(logDialog)
        self.buttonBox.accepted.connect(logDialog.accept)
        self.buttonBox.rejected.connect(logDialog.reject)

        QMetaObject.connectSlotsByName(logDialog)
    # setupUi

    def retranslateUi(self, logDialog: QDialog) -> None:
        logDialog.setWindowTitle(QCoreApplication.translate("logDialog", u"Logs", None))
    # retranslateUi

