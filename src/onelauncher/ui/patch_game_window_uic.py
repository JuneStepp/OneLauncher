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

class Ui_patchGameWindow(object):
    def setupUi(self, patchGameWindow: QDialog) -> None:
        if not patchGameWindow.objectName():
            patchGameWindow.setObjectName(u"patchGameWindow")
        patchGameWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        patchGameWindow.resize(720, 400)
        patchGameWindow.setModal(True)
        self.verticalLayout = QVBoxLayout(patchGameWindow)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.txtLog = QTextBrowser(patchGameWindow)
        self.txtLog.setObjectName(u"txtLog")

        self.verticalLayout.addWidget(self.txtLog)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.progressBar = QProgressBar(patchGameWindow)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.horizontalLayout.addWidget(self.progressBar)

        self.btnStart = QPushButton(patchGameWindow)
        self.btnStart.setObjectName(u"btnStart")

        self.horizontalLayout.addWidget(self.btnStart)

        self.btnStop = QPushButton(patchGameWindow)
        self.btnStop.setObjectName(u"btnStop")

        self.horizontalLayout.addWidget(self.btnStop)


        self.verticalLayout.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.btnStart, self.btnStop)
        QWidget.setTabOrder(self.btnStop, self.txtLog)

        self.retranslateUi(patchGameWindow)

        QMetaObject.connectSlotsByName(patchGameWindow)
    # setupUi

    def retranslateUi(self, patchGameWindow: QDialog) -> None:
        patchGameWindow.setWindowTitle(QCoreApplication.translate("patchGameWindow", u"MainWindow", None))
        self.progressBar.setFormat(QCoreApplication.translate("patchGameWindow", u"%p% (%v/%m)", None))
        self.btnStart.setText(QCoreApplication.translate("patchGameWindow", u"Start", None))
        self.btnStop.setText(QCoreApplication.translate("patchGameWindow", u"Stop", None))
    # retranslateUi

