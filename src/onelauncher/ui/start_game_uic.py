# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'start_game.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QPushButton,
    QSizePolicy, QSpacerItem, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_startGameDialog(object):
    def setupUi(self, startGameDialog: QDialog) -> None:
        if not startGameDialog.objectName():
            startGameDialog.setObjectName(u"startGameDialog")
        startGameDialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        startGameDialog.resize(720, 400)
        startGameDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(startGameDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.txtLog = QTextBrowser(startGameDialog)
        self.txtLog.setObjectName(u"txtLog")

        self.verticalLayout.addWidget(self.txtLog)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.btnStart = QPushButton(startGameDialog)
        self.btnStart.setObjectName(u"btnStart")

        self.horizontalLayout.addWidget(self.btnStart)

        self.btnStop = QPushButton(startGameDialog)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout.addWidget(self.btnStop)

        self.btnSave = QPushButton(startGameDialog)
        self.btnSave.setObjectName(u"btnSave")

        self.horizontalLayout.addWidget(self.btnSave)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(startGameDialog)

        QMetaObject.connectSlotsByName(startGameDialog)
    # setupUi

    def retranslateUi(self, startGameDialog: QDialog) -> None:
        startGameDialog.setWindowTitle(QCoreApplication.translate("startGameDialog", u"MainWindow", None))
        self.btnStart.setText(QCoreApplication.translate("startGameDialog", u"Start", None))
        self.btnStop.setText(QCoreApplication.translate("startGameDialog", u"Stop", None))
        self.btnSave.setText(QCoreApplication.translate("startGameDialog", u"Save Log", None))
    # retranslateUi

