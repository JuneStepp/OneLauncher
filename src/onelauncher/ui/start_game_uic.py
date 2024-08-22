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

        self.btnAbort = QPushButton(startGameDialog)
        self.btnAbort.setObjectName(u"btnAbort")

        self.horizontalLayout.addWidget(self.btnAbort)

        self.btnQuit = QPushButton(startGameDialog)
        self.btnQuit.setObjectName(u"btnQuit")

        self.horizontalLayout.addWidget(self.btnQuit)


        self.verticalLayout.addLayout(self.horizontalLayout)

        QWidget.setTabOrder(self.btnAbort, self.btnQuit)
        QWidget.setTabOrder(self.btnQuit, self.txtLog)

        self.retranslateUi(startGameDialog)

        QMetaObject.connectSlotsByName(startGameDialog)
    # setupUi

    def retranslateUi(self, startGameDialog: QDialog) -> None:
        startGameDialog.setWindowTitle(QCoreApplication.translate("startGameDialog", u"MainWindow", None))
        self.btnAbort.setText(QCoreApplication.translate("startGameDialog", u"Abort", None))
        self.btnQuit.setText(QCoreApplication.translate("startGameDialog", u"Quit", None))
    # retranslateUi

