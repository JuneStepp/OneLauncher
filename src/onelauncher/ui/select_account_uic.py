# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_account.ui'
##
## Created by: Qt User Interface Compiler version 6.1.3
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
        dlgChooseAccount.resize(320, 169)
        font = QFont()
        font.setPointSize(12)
        dlgChooseAccount.setFont(font)
        dlgChooseAccount.setModal(True)
        self.accountsComboBox = QComboBox(dlgChooseAccount)
        self.accountsComboBox.setObjectName(u"accountsComboBox")
        self.accountsComboBox.setGeometry(QRect(5, 90, 310, 33))
        self.label = QLabel(dlgChooseAccount)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(-5, 8, 331, 71))
        self.label.setAlignment(Qt.AlignCenter)
        self.buttonBox = QDialogButtonBox(dlgChooseAccount)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(145, 135, 166, 27))
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Ok)
        self.saveSelectionCheckBox = QCheckBox(dlgChooseAccount)
        self.saveSelectionCheckBox.setObjectName(u"saveSelectionCheckBox")
        self.saveSelectionCheckBox.setGeometry(QRect(4, 138, 141, 21))

        self.retranslateUi(dlgChooseAccount)
        self.buttonBox.accepted.connect(dlgChooseAccount.accept)
        self.buttonBox.rejected.connect(dlgChooseAccount.reject)

        QMetaObject.connectSlotsByName(dlgChooseAccount)
    # setupUi

    def retranslateUi(self, dlgChooseAccount):
        dlgChooseAccount.setWindowTitle(QCoreApplication.translate("dlgChooseAccount", u"Choose Account", None))
        self.label.setText(QCoreApplication.translate("dlgChooseAccount", u"Multiple game accounts found\n"
"\n"
"Please select one", None))
        self.saveSelectionCheckBox.setText(QCoreApplication.translate("dlgChooseAccount", u"Save Selection", None))
    # retranslateUi

