# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'patching_window.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QProgressBar,
    QPushButton, QSizePolicy, QTextBrowser, QVBoxLayout,
    QWidget)

class Ui_patchingDialog(object):
    def setupUi(self, patchingDialog: QDialog) -> None:
        if not patchingDialog.objectName():
            patchingDialog.setObjectName(u"patchingDialog")
        patchingDialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        patchingDialog.resize(720, 400)
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

        self.btnStart = QPushButton(patchingDialog)
        self.btnStart.setObjectName(u"btnStart")

        self.horizontalLayout.addWidget(self.btnStart)

        self.btnStop = QPushButton(patchingDialog)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout.addWidget(self.btnStop)


        self.verticalLayout.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.btnStart, self.btnStop)
        QWidget.setTabOrder(self.btnStop, self.txtLog)

        self.retranslateUi(patchingDialog)

        QMetaObject.connectSlotsByName(patchingDialog)
    # setupUi

    def retranslateUi(self, patchingDialog: QDialog) -> None:
        patchingDialog.setWindowTitle(QCoreApplication.translate("patchingDialog", u"MainWindow", None))
        self.progressBar.setFormat(QCoreApplication.translate("patchingDialog", u"%p% (%v/%m)", None))
        self.btnStart.setText(QCoreApplication.translate("patchingDialog", u"Start", None))
        self.btnStop.setText(QCoreApplication.translate("patchingDialog", u"Stop", None))
    # retranslateUi

