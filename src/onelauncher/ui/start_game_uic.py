# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'start_game.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_startGameDialog(object):
    def setupUi(self, startGameDialog):
        if not startGameDialog.objectName():
            startGameDialog.setObjectName(u"startGameDialog")
        startGameDialog.setWindowModality(Qt.ApplicationModal)
        startGameDialog.resize(720, 400)
        font = QFont()
        font.setPointSize(12)
        startGameDialog.setFont(font)
        startGameDialog.setModal(True)
        self.txtLog = QTextBrowser(startGameDialog)
        self.txtLog.setObjectName(u"txtLog")
        self.txtLog.setGeometry(QRect(5, 5, 710, 351))
        self.btnSave = QPushButton(startGameDialog)
        self.btnSave.setObjectName(u"btnSave")
        self.btnSave.setGeometry(QRect(625, 361, 90, 34))
        self.btnStop = QPushButton(startGameDialog)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setGeometry(QRect(530, 361, 90, 34))
        self.btnStart = QPushButton(startGameDialog)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setGeometry(QRect(435, 361, 90, 34))

        self.retranslateUi(startGameDialog)

        QMetaObject.connectSlotsByName(startGameDialog)
    # setupUi

    def retranslateUi(self, startGameDialog):
        startGameDialog.setWindowTitle(QCoreApplication.translate("startGameDialog", u"MainWindow", None))
        self.btnSave.setText(QCoreApplication.translate("startGameDialog", u"Save", None))
        self.btnStop.setText(QCoreApplication.translate("startGameDialog", u"Stop", None))
        self.btnStart.setText(QCoreApplication.translate("startGameDialog", u"Start", None))
    # retranslateUi

