# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'install_game.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QAbstractScrollArea, QApplication, QDialogButtonBox,
    QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QListView, QListWidget, QListWidgetItem, QProgressBar,
    QSizePolicy, QVBoxLayout, QWidget)

from .custom_widgets import (FramelessQDialogWithStylePreview, NoOddSizesQToolButton)
from .qtdesigner.custom_widgets import QDialogWithStylePreview

class Ui_installGameWindow(object):
    def setupUi(self, installGameWindow: FramelessQDialogWithStylePreview) -> None:
        if not installGameWindow.objectName():
            installGameWindow.setObjectName(u"installGameWindow")
        installGameWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        installGameWindow.resize(468, 273)
        installGameWindow.setModal(True)
        self.verticalLayout = QVBoxLayout(installGameWindow)
        self.verticalLayout.setSpacing(9)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widgetInstallOptions = QWidget(installGameWindow)
        self.widgetInstallOptions.setObjectName(u"widgetInstallOptions")
        self.formLayout = QFormLayout(self.widgetInstallOptions)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        self.installDirLayout = QHBoxLayout()
        self.installDirLayout.setObjectName(u"installDirLayout")
        self.installDirLineEdit = QLineEdit(self.widgetInstallOptions)
        self.installDirLineEdit.setObjectName(u"installDirLineEdit")

        self.installDirLayout.addWidget(self.installDirLineEdit)

        self.selectInstallDirButton = NoOddSizesQToolButton(self.widgetInstallOptions)
        self.selectInstallDirButton.setObjectName(u"selectInstallDirButton")
        self.selectInstallDirButton.setArrowType(Qt.ArrowType.NoArrow)

        self.installDirLayout.addWidget(self.selectInstallDirButton)


        self.formLayout.setLayout(1, QFormLayout.ItemRole.FieldRole, self.installDirLayout)

        self.installDirLabel = QLabel(self.widgetInstallOptions)
        self.installDirLabel.setObjectName(u"installDirLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.installDirLabel)

        self.gameTypeListWidget = QListWidget(self.widgetInstallOptions)
        self.gameTypeListWidget.setObjectName(u"gameTypeListWidget")
        self.gameTypeListWidget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.gameTypeListWidget.setResizeMode(QListView.ResizeMode.Adjust)

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.gameTypeListWidget)

        self.gameTypeLabel = QLabel(self.widgetInstallOptions)
        self.gameTypeLabel.setObjectName(u"gameTypeLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.gameTypeLabel)


        self.verticalLayout.addWidget(self.widgetInstallOptions)

        self.progressBar = QProgressBar(installGameWindow)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setValue(24)

        self.verticalLayout.addWidget(self.progressBar)

        self.buttonBox = QDialogButtonBox(installGameWindow)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(installGameWindow)
        self.buttonBox.rejected.connect(installGameWindow.reject)

        QMetaObject.connectSlotsByName(installGameWindow)
    # setupUi

    def retranslateUi(self, installGameWindow: FramelessQDialogWithStylePreview) -> None:
        installGameWindow.setWindowTitle(QCoreApplication.translate("installGameWindow", u"Install Game", None))
#if QT_CONFIG(tooltip)
        self.installDirLineEdit.setToolTip(QCoreApplication.translate("installGameWindow", u"Directory where the game will be installed", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.selectInstallDirButton.setToolTip(QCoreApplication.translate("installGameWindow", u"Select game install directory from the file browser", None))
#endif // QT_CONFIG(tooltip)
        self.selectInstallDirButton.setProperty(u"qssClass", [
            QCoreApplication.translate("installGameWindow", u"icon-base", None)])
#if QT_CONFIG(tooltip)
        self.installDirLabel.setToolTip(QCoreApplication.translate("installGameWindow", u"Directory where the game will be installed", None))
#endif // QT_CONFIG(tooltip)
        self.installDirLabel.setText(QCoreApplication.translate("installGameWindow", u"Install Directory", None))
#if QT_CONFIG(tooltip)
        self.gameTypeListWidget.setToolTip(QCoreApplication.translate("installGameWindow", u"Which game to install", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.gameTypeLabel.setToolTip(QCoreApplication.translate("installGameWindow", u"Which game to install", None))
#endif // QT_CONFIG(tooltip)
        self.gameTypeLabel.setText(QCoreApplication.translate("installGameWindow", u"Game Type", None))
    # retranslateUi

