# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'patching_window.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_patchingWindow(object):
    def setupUi(self, patchingDialog):
        if not patchingDialog.objectName():
            patchingDialog.setObjectName(u"patchingDialog")
        patchingDialog.setWindowModality(Qt.ApplicationModal)
        patchingDialog.resize(720, 400)
        font = QFont()
        font.setFamilies([u"Verdana"])
        font.setPointSize(12)
        patchingDialog.setFont(font)
        patchingDialog.setModal(True)
        self.verticalLayout = QVBoxLayout(patchingDialog)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.txtLog = QTextBrowser(patchingDialog)
        self.txtLog.setObjectName(u"txtLog")

        self.verticalLayout.addWidget(self.txtLog)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.progressBar = QProgressBar(patchingDialog)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.horizontalLayout.addWidget(self.progressBar)

        self.btnStop = QPushButton(patchingDialog)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout.addWidget(self.btnStop)

        self.btnSave = QPushButton(patchingDialog)
        self.btnSave.setObjectName(u"btnSave")

        self.horizontalLayout.addWidget(self.btnSave)

        self.btnStart = QPushButton(patchingDialog)
        self.btnStart.setObjectName(u"btnStart")

        self.horizontalLayout.addWidget(self.btnStart)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(patchingDialog)

        QMetaObject.connectSlotsByName(patchingDialog)
    # setupUi

    def retranslateUi(self, patchingDialog):
        patchingDialog.setWindowTitle(QCoreApplication.translate("patchingWindow", u"MainWindow", None))
        self.progressBar.setFormat(QCoreApplication.translate("patchingWindow", u"%p% (%v/%m)", None))
        self.btnStop.setText(QCoreApplication.translate("patchingWindow", u"Stop", None))
        self.btnSave.setText(QCoreApplication.translate("patchingWindow", u"Save", None))
        self.btnStart.setText(QCoreApplication.translate("patchingWindow", u"Start", None))
    # retranslateUi

