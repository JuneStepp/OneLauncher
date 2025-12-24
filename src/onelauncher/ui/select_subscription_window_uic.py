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

class Ui_selectSubscriptionWindow(object):
    def setupUi(self, selectSubscriptionWindow: QDialog) -> None:
        if not selectSubscriptionWindow.objectName():
            selectSubscriptionWindow.setObjectName(u"selectSubscriptionWindow")
        selectSubscriptionWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        selectSubscriptionWindow.resize(320, 169)
        selectSubscriptionWindow.setModal(True)
        self.verticalLayout = QVBoxLayout(selectSubscriptionWindow)
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(selectSubscriptionWindow)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.subscriptionsComboBox = QComboBox(selectSubscriptionWindow)
        self.subscriptionsComboBox.setObjectName(u"subscriptionsComboBox")

        self.verticalLayout.addWidget(self.subscriptionsComboBox)

        self.buttonBox = QDialogButtonBox(selectSubscriptionWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)

#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.subscriptionsComboBox)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(selectSubscriptionWindow)
        self.buttonBox.accepted.connect(selectSubscriptionWindow.accept)
        self.buttonBox.rejected.connect(selectSubscriptionWindow.reject)

        QMetaObject.connectSlotsByName(selectSubscriptionWindow)
    # setupUi

    def retranslateUi(self, selectSubscriptionWindow: QDialog) -> None:
        selectSubscriptionWindow.setWindowTitle(QCoreApplication.translate("selectSubscriptionWindow", u"Select Subscription", None))
        self.label.setText(QCoreApplication.translate("selectSubscriptionWindow", u"Multiple game sub-accounts found\n"
"\n"
"Please select one", None))
    # retranslateUi

