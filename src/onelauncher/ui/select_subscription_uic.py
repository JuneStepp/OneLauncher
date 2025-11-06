# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'select_subscription.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
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
    QDialogButtonBox, QLabel, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_dlgSelectSubscription(object):
    def setupUi(self, dlgSelectSubscription: QDialog) -> None:
        if not dlgSelectSubscription.objectName():
            dlgSelectSubscription.setObjectName(u"dlgSelectSubscription")
        dlgSelectSubscription.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlgSelectSubscription.resize(320, 169)
        dlgSelectSubscription.setModal(True)
        self.verticalLayout = QVBoxLayout(dlgSelectSubscription)
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(dlgSelectSubscription)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.subscriptionsComboBox = QComboBox(dlgSelectSubscription)
        self.subscriptionsComboBox.setObjectName(u"subscriptionsComboBox")

        self.verticalLayout.addWidget(self.subscriptionsComboBox)

        self.buttonBox = QDialogButtonBox(dlgSelectSubscription)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.subscriptionsComboBox)
#endif // QT_CONFIG(shortcut)

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

