# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
##
## Created by: Qt User Interface Compiler version 6.4.2
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
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_dlgAbout(object):
    def setupUi(self, dlgAbout: QDialog) -> None:
        if not dlgAbout.objectName():
            dlgAbout.setObjectName(u"dlgAbout")
        dlgAbout.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlgAbout.resize(520, 320)
        font = QFont()
        font.setFamilies([u"Verdana"])
        font.setPointSize(12)
        dlgAbout.setFont(font)
        dlgAbout.setModal(True)
        self.buttonBox = QDialogButtonBox(dlgAbout)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(10, 280, 500, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)
        self.layoutWidget = QWidget(dlgAbout)
        self.layoutWidget.setObjectName(u"layoutWidget")
        self.layoutWidget.setGeometry(QRect(10, 10, 501, 261))
        self.verticalLayout = QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 1, 0, 0)
        self.lblDescription = QLabel(self.layoutWidget)
        self.lblDescription.setObjectName(u"lblDescription")
        self.lblDescription.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblDescription)

        self.lblRepoWebsite = QLabel(self.layoutWidget)
        self.lblRepoWebsite.setObjectName(u"lblRepoWebsite")
        self.lblRepoWebsite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblRepoWebsite.setOpenExternalLinks(True)
        self.lblRepoWebsite.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.lblRepoWebsite)

        self.lblCopyright = QLabel(self.layoutWidget)
        self.lblCopyright.setObjectName(u"lblCopyright")
        self.lblCopyright.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblCopyright)

        self.lblCopyrightHistory = QLabel(self.layoutWidget)
        self.lblCopyrightHistory.setObjectName(u"lblCopyrightHistory")
        self.lblCopyrightHistory.setAcceptDrops(False)
        self.lblCopyrightHistory.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblCopyrightHistory)

        self.lblVersion = QLabel(self.layoutWidget)
        self.lblVersion.setObjectName(u"lblVersion")
        self.lblVersion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblVersion)


        self.retranslateUi(dlgAbout)
        self.buttonBox.clicked.connect(dlgAbout.accept)

        QMetaObject.connectSlotsByName(dlgAbout)
    # setupUi

    def retranslateUi(self, dlgAbout: QDialog) -> None:
        dlgAbout.setWindowTitle(QCoreApplication.translate("dlgAbout", u"About", None))
        self.lblDescription.setText("")
        self.lblRepoWebsite.setText("")
        self.lblCopyright.setText("")
        self.lblCopyrightHistory.setText("")
        self.lblVersion.setText("")
    # retranslateUi

