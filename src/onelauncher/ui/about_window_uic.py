# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'about.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QSizePolicy, QSpacerItem, QVBoxLayout,
    QWidget)

class Ui_aboutWindow(object):
    def setupUi(self, aboutWindow: QDialog) -> None:
        if not aboutWindow.objectName():
            aboutWindow.setObjectName(u"aboutWindow")
        aboutWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        aboutWindow.resize(400, 250)
        aboutWindow.setModal(True)
        self.verticalLayout_2 = QVBoxLayout(aboutWindow)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(12, 12, 12, 12)
        self.lblDescription = QLabel(aboutWindow)
        self.lblDescription.setObjectName(u"lblDescription")
        self.lblDescription.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblDescription)

        self.lblRepoWebsite = QLabel(aboutWindow)
        self.lblRepoWebsite.setObjectName(u"lblRepoWebsite")
        self.lblRepoWebsite.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblRepoWebsite.setOpenExternalLinks(True)
        self.lblRepoWebsite.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

        self.verticalLayout.addWidget(self.lblRepoWebsite)

        self.lblCopyright = QLabel(aboutWindow)
        self.lblCopyright.setObjectName(u"lblCopyright")
        self.lblCopyright.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblCopyright)

        self.lblCopyrightHistory = QLabel(aboutWindow)
        self.lblCopyrightHistory.setObjectName(u"lblCopyrightHistory")
        self.lblCopyrightHistory.setAcceptDrops(False)
        self.lblCopyrightHistory.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblCopyrightHistory)

        self.lblVersion = QLabel(aboutWindow)
        self.lblVersion.setObjectName(u"lblVersion")
        self.lblVersion.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.lblVersion)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.verticalLayout_2.addLayout(self.verticalLayout)

        self.buttonBox = QDialogButtonBox(aboutWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Close)

        self.verticalLayout_2.addWidget(self.buttonBox)


        self.retranslateUi(aboutWindow)
        self.buttonBox.clicked.connect(aboutWindow.accept)

        QMetaObject.connectSlotsByName(aboutWindow)
    # setupUi

    def retranslateUi(self, aboutWindow: QDialog) -> None:
        aboutWindow.setWindowTitle(QCoreApplication.translate("aboutWindow", u"About", None))
        self.lblDescription.setText("")
        self.lblRepoWebsite.setText("")
        self.lblCopyright.setText("")
        self.lblCopyrightHistory.setText("")
        self.lblVersion.setText("")
    # retranslateUi

