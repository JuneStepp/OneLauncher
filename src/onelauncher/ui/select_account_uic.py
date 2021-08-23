# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_account.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


class Ui_dlgChooseAccount(object):
    def setupUi(self, dlgChooseAccount):
        if not dlgChooseAccount.objectName():
            dlgChooseAccount.setObjectName(u"dlgChooseAccount")
        dlgChooseAccount.setWindowModality(Qt.ApplicationModal)
        dlgChooseAccount.resize(320, 205)
        font = QFont()
        font.setFamilies([u"Verdana"])
        font.setPointSize(12)
        dlgChooseAccount.setFont(font)
        dlgChooseAccount.setModal(True)
        self.lblMessage = QLabel(dlgChooseAccount)
        self.lblMessage.setObjectName(u"lblMessage")
        self.lblMessage.setGeometry(QRect(5, 5, 291, 121))
        self.comboBox = QComboBox(dlgChooseAccount)
        self.comboBox.setObjectName(u"comboBox")
        self.comboBox.setGeometry(QRect(5, 117, 310, 33))
        self.btnOK = QPushButton(dlgChooseAccount)
        self.btnOK.setObjectName(u"btnOK")
        self.btnOK.setGeometry(QRect(225, 160, 90, 33))
        self.btnCancel = QPushButton(dlgChooseAccount)
        self.btnCancel.setObjectName(u"btnCancel")
        self.btnCancel.setGeometry(QRect(130, 160, 90, 33))

        self.retranslateUi(dlgChooseAccount)
        self.btnOK.clicked.connect(dlgChooseAccount.accept)
        self.btnCancel.clicked.connect(dlgChooseAccount.reject)

        QMetaObject.connectSlotsByName(dlgChooseAccount)
    # setupUi

    def retranslateUi(self, dlgChooseAccount):
        dlgChooseAccount.setWindowTitle(QCoreApplication.translate("dlgChooseAccount", u"Choose Account", None))
        self.lblMessage.setText("")
        self.btnOK.setText(QCoreApplication.translate("dlgChooseAccount", u"OK", None))
        self.btnCancel.setText(QCoreApplication.translate("dlgChooseAccount", u"Cancel", None))
    # retranslateUi

