# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'error_message.ui'
##
## Created by: Qt User Interface Compiler version 6.7.0
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

class Ui_errorDialog(object):
    def setupUi(self, errorDialog):
        if not errorDialog.objectName():
            errorDialog.setObjectName(u"errorDialog")
        errorDialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        errorDialog.resize(400, 300)
        errorDialog.setSizeGripEnabled(True)
        errorDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(errorDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.textLabel = QLabel(errorDialog)
        self.textLabel.setObjectName(u"textLabel")

        self.verticalLayout.addWidget(self.textLabel)

        self.detailsTextEdit = QPlainTextEdit(errorDialog)
        self.detailsTextEdit.setObjectName(u"detailsTextEdit")
        self.detailsTextEdit.setUndoRedoEnabled(False)
        self.detailsTextEdit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.detailsTextEdit.setReadOnly(True)

        self.verticalLayout.addWidget(self.detailsTextEdit)

        self.buttonBox = QDialogButtonBox(errorDialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(errorDialog)
        self.buttonBox.accepted.connect(errorDialog.accept)
        self.buttonBox.rejected.connect(errorDialog.reject)

        QMetaObject.connectSlotsByName(errorDialog)
    # setupUi

    def retranslateUi(self, errorDialog):
        errorDialog.setWindowTitle(QCoreApplication.translate("errorDialog", u"Error", None))
        self.textLabel.setText(QCoreApplication.translate("errorDialog", u"Error:", None))
    # retranslateUi

