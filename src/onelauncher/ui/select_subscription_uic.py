# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_subscription.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QComboBox, QDialog,
    QDialogButtonBox, QLabel, QSizePolicy, QWidget)

class Ui_dlgSelectSubscription(object):
    def setupUi(self, dlgSelectSubscription: QDialog) -> None:
        if not dlgSelectSubscription.objectName():
            dlgSelectSubscription.setObjectName(u"dlgSelectSubscription")
        dlgSelectSubscription.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlgSelectSubscription.resize(320, 169)
        font = QFont()
        font.setPointSize(12)
        dlgSelectSubscription.setFont(font)
        dlgSelectSubscription.setModal(True)
        self.subscriptionsComboBox = QComboBox(dlgSelectSubscription)
        self.subscriptionsComboBox.setObjectName(u"subscriptionsComboBox")
        self.subscriptionsComboBox.setGeometry(QRect(5, 90, 310, 33))
        self.label = QLabel(dlgSelectSubscription)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(-5, 8, 331, 71))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.buttonBox = QDialogButtonBox(dlgSelectSubscription)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(145, 135, 166, 27))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.retranslateUi(dlgSelectSubscription)
        self.buttonBox.accepted.connect(dlgSelectSubscription.accept)
        self.buttonBox.rejected.connect(dlgSelectSubscription.reject)

        QMetaObject.connectSlotsByName(dlgSelectSubscription)
    # setupUi

    def retranslateUi(self, dlgSelectSubscription: QDialog) -> None:
        dlgSelectSubscription.setWindowTitle(QCoreApplication.translate("dlgSelectSubscription", u"Select Subscription", None))
        self.label.setText(QCoreApplication.translate("dlgSelectSubscription", u"Multiple game sub-accounts found\n"
"\n"
"Please select one", None))
    # retranslateUi

