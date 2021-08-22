# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'winLog.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_winLog(object):
    def setupUi(self, winLog):
        if not winLog.objectName():
            winLog.setObjectName(u"winLog")
        winLog.setWindowModality(Qt.ApplicationModal)
        winLog.resize(720, 400)
        font = QFont()
        font.setFamilies([u"Verdana"])
        font.setPointSize(12)
        winLog.setFont(font)
        winLog.setModal(True)
        self.txtLog = QTextBrowser(winLog)
        self.txtLog.setObjectName(u"txtLog")
        self.txtLog.setGeometry(QRect(5, 5, 710, 351))
        self.btnSave = QPushButton(winLog)
        self.btnSave.setObjectName(u"btnSave")
        self.btnSave.setGeometry(QRect(625, 361, 90, 34))
        self.btnStop = QPushButton(winLog)
        self.btnStop.setObjectName(u"btnStop")
        self.btnStop.setGeometry(QRect(530, 361, 90, 34))
        self.btnStart = QPushButton(winLog)
        self.btnStart.setObjectName(u"btnStart")
        self.btnStart.setGeometry(QRect(435, 361, 90, 34))

        self.retranslateUi(winLog)

        QMetaObject.connectSlotsByName(winLog)
    # setupUi

    def retranslateUi(self, winLog):
        winLog.setWindowTitle(QCoreApplication.translate("winLog", u"MainWindow", None))
        self.btnSave.setText(QCoreApplication.translate("winLog", u"Save", None))
        self.btnStop.setText(QCoreApplication.translate("winLog", u"Stop", None))
        self.btnStart.setText(QCoreApplication.translate("winLog", u"Start", None))
    # retranslateUi

