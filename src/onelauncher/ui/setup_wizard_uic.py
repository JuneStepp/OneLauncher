# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_wizard.ui'
##
## Created by: Qt User Interface Compiler version 6.5.1
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFormLayout,
    QFrame, QHBoxLayout, QLabel, QLayout,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget, QWizard,
    QWizardPage)

class Ui_Wizard(object):
    def setupUi(self, Wizard):
        if not Wizard.objectName():
            Wizard.setObjectName(u"Wizard")
        Wizard.resize(621, 411)
        self.languageSelectionWizardPage = QWizardPage()
        self.languageSelectionWizardPage.setObjectName(u"languageSelectionWizardPage")
        self.verticalLayoutWidget = QWidget(self.languageSelectionWizardPage)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(10, 10, 211, 251))
        self.verticalLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel(self.verticalLayoutWidget)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.languagesListWidget = QListWidget(self.verticalLayoutWidget)
        self.languagesListWidget.setObjectName(u"languagesListWidget")
        self.languagesListWidget.setFrameShape(QFrame.Box)
        self.languagesListWidget.setEditTriggers(QAbstractItemView.CurrentChanged|QAbstractItemView.DoubleClicked|QAbstractItemView.EditKeyPressed|QAbstractItemView.SelectedClicked)
        self.languagesListWidget.setProperty("showDropIndicator", False)
        self.languagesListWidget.setWordWrap(True)
        self.languagesListWidget.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.languagesListWidget)

        self.formLayoutWidget = QWidget(self.languageSelectionWizardPage)
        self.formLayoutWidget.setObjectName(u"formLayoutWidget")
        self.formLayoutWidget.setGeometry(QRect(249, 39, 331, 221))
        self.formLayout = QFormLayout(self.formLayoutWidget)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setSizeConstraint(QLayout.SetMaximumSize)
        self.formLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.formLayout.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.formLayout.setContentsMargins(0, 12, 0, 0)
        self.alwaysUseDefaultLangForUILabel = QLabel(self.formLayoutWidget)
        self.alwaysUseDefaultLangForUILabel.setObjectName(u"alwaysUseDefaultLangForUILabel")

        self.formLayout.setWidget(0, QFormLayout.LabelRole, self.alwaysUseDefaultLangForUILabel)

        self.alwaysUseDefaultLangForUICheckBox = QCheckBox(self.formLayoutWidget)
        self.alwaysUseDefaultLangForUICheckBox.setObjectName(u"alwaysUseDefaultLangForUICheckBox")

        self.formLayout.setWidget(0, QFormLayout.FieldRole, self.alwaysUseDefaultLangForUICheckBox)

        Wizard.setPage(0, self.languageSelectionWizardPage)
        self.gamesSelectionWizardPage = QWizardPage()
        self.gamesSelectionWizardPage.setObjectName(u"gamesSelectionWizardPage")
        self.verticalLayoutWidget_2 = QWidget(self.gamesSelectionWizardPage)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(-20, -2, 631, 271))
        self.gamesSelectionLayout = QVBoxLayout(self.verticalLayoutWidget_2)
        self.gamesSelectionLayout.setObjectName(u"gamesSelectionLayout")
        self.gamesSelectionLayout.setContentsMargins(35, 10, 35, 10)
        self.gamesListWidget = QListWidget(self.verticalLayoutWidget_2)
        self.gamesListWidget.setObjectName(u"gamesListWidget")
        self.gamesListWidget.setDragEnabled(True)
        self.gamesListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.gamesListWidget.setDefaultDropAction(Qt.TargetMoveAction)
        self.gamesListWidget.setAlternatingRowColors(True)
        self.gamesListWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.gamesListWidget.setSelectionBehavior(QAbstractItemView.SelectItems)

        self.gamesSelectionLayout.addWidget(self.gamesListWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.downPriorityButton = QPushButton(self.verticalLayoutWidget_2)
        self.downPriorityButton.setObjectName(u"downPriorityButton")

        self.horizontalLayout.addWidget(self.downPriorityButton)

        self.upPriorityButton = QPushButton(self.verticalLayoutWidget_2)
        self.upPriorityButton.setObjectName(u"upPriorityButton")

        self.horizontalLayout.addWidget(self.upPriorityButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.horizontalLayout.addItem(self.verticalSpacer)

        self.addGameButton = QPushButton(self.verticalLayoutWidget_2)
        self.addGameButton.setObjectName(u"addGameButton")

        self.horizontalLayout.addWidget(self.addGameButton)


        self.gamesSelectionLayout.addLayout(self.horizontalLayout)

        Wizard.setPage(1, self.gamesSelectionWizardPage)
        self.finishedWizardPage = QWizardPage()
        self.finishedWizardPage.setObjectName(u"finishedWizardPage")
        Wizard.setPage(3, self.finishedWizardPage)

        self.retranslateUi(Wizard)

        QMetaObject.connectSlotsByName(Wizard)
    # setupUi

    def retranslateUi(self, Wizard):
        Wizard.setWindowTitle(QCoreApplication.translate("Wizard", u"Wizard", None))
        self.languageSelectionWizardPage.setTitle(QCoreApplication.translate("Wizard", u"OneLauncher Setup Wizard:", None))
        self.languageSelectionWizardPage.setSubTitle(QCoreApplication.translate("Wizard", u"This wizard will quickly take you through the steps needed to get up and running with OneLauncher. ", None))
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("Wizard", u"The language used for games by default", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("Wizard", u"Default Language", None))
#if QT_CONFIG(tooltip)
        self.languagesListWidget.setToolTip(QCoreApplication.translate("Wizard", u"The language used for games by default", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.alwaysUseDefaultLangForUILabel.setToolTip(QCoreApplication.translate("Wizard", u"Always show OneLauncher interface in default language", None))
#endif // QT_CONFIG(tooltip)
        self.alwaysUseDefaultLangForUILabel.setText(QCoreApplication.translate("Wizard", u"Always Use Default Language For UI", None))
        self.gamesSelectionWizardPage.setTitle(QCoreApplication.translate("Wizard", u"Games Selection", None))
        self.gamesSelectionWizardPage.setSubTitle(QCoreApplication.translate("Wizard", u"Select your game installations. The first one will be the main game instance.", None))
#if QT_CONFIG(tooltip)
        self.downPriorityButton.setToolTip(QCoreApplication.translate("Wizard", u"Decrease priority", None))
#endif // QT_CONFIG(tooltip)
        self.downPriorityButton.setText(QCoreApplication.translate("Wizard", u"\u2193", None))
#if QT_CONFIG(tooltip)
        self.upPriorityButton.setToolTip(QCoreApplication.translate("Wizard", u"Increase priority", None))
#endif // QT_CONFIG(tooltip)
        self.upPriorityButton.setText(QCoreApplication.translate("Wizard", u"\u2191", None))
        self.addGameButton.setText(QCoreApplication.translate("Wizard", u"Add Game", None))
        self.finishedWizardPage.setTitle(QCoreApplication.translate("Wizard", u"Setup Finished", None))
        self.finishedWizardPage.setSubTitle(QCoreApplication.translate("Wizard", u"That's it! You can always check out the settings menu or addons manager for extra customization.", None))
    # retranslateUi

