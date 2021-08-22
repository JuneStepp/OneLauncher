# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_wizard.ui'
##
## Created by: Qt User Interface Compiler version 6.1.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *  # type: ignore
from PySide6.QtGui import *  # type: ignore
from PySide6.QtWidgets import *  # type: ignore


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
        self.verticalLayoutWidget_2.setGeometry(QRect(-20, -3, 631, 292))
        self.gamesSelectionLayout = QVBoxLayout(self.verticalLayoutWidget_2)
        self.gamesSelectionLayout.setObjectName(u"gamesSelectionLayout")
        self.gamesSelectionLayout.setContentsMargins(35, 10, 35, 10)
        self.lotroLabel = QLabel(self.verticalLayoutWidget_2)
        self.lotroLabel.setObjectName(u"lotroLabel")
        self.lotroLabel.setAlignment(Qt.AlignCenter)

        self.gamesSelectionLayout.addWidget(self.lotroLabel)

        self.lotroListWidget = QListWidget(self.verticalLayoutWidget_2)
        font = QFont()
        font.setBold(False)
        font.setItalic(True)
        __qlistwidgetitem = QListWidgetItem(self.lotroListWidget)
        __qlistwidgetitem.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem.setFont(font);
        __qlistwidgetitem.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        self.lotroListWidget.setObjectName(u"lotroListWidget")
        self.lotroListWidget.setDragEnabled(True)
        self.lotroListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.lotroListWidget.setDefaultDropAction(Qt.TargetMoveAction)
        self.lotroListWidget.setAlternatingRowColors(True)
        self.lotroListWidget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.gamesSelectionLayout.addWidget(self.lotroListWidget)

        self.ddoLabel = QLabel(self.verticalLayoutWidget_2)
        self.ddoLabel.setObjectName(u"ddoLabel")
        self.ddoLabel.setAlignment(Qt.AlignCenter)

        self.gamesSelectionLayout.addWidget(self.ddoLabel)

        self.ddoListWidget = QListWidget(self.verticalLayoutWidget_2)
        __qlistwidgetitem1 = QListWidgetItem(self.ddoListWidget)
        __qlistwidgetitem1.setTextAlignment(Qt.AlignCenter);
        __qlistwidgetitem1.setFont(font);
        __qlistwidgetitem1.setFlags(Qt.ItemIsUserCheckable|Qt.ItemIsEnabled);
        self.ddoListWidget.setObjectName(u"ddoListWidget")
        self.ddoListWidget.setDragEnabled(True)
        self.ddoListWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.ddoListWidget.setDefaultDropAction(Qt.TargetMoveAction)
        self.ddoListWidget.setAlternatingRowColors(True)
        self.ddoListWidget.setSelectionMode(QAbstractItemView.MultiSelection)

        self.gamesSelectionLayout.addWidget(self.ddoListWidget)

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
        self.alwaysUseDefaultLangForUILabel.setText(QCoreApplication.translate("Wizard", u"Always Keep UI in Default Language", None))
        self.gamesSelectionWizardPage.setTitle(QCoreApplication.translate("Wizard", u"Games Selection", None))
        self.gamesSelectionWizardPage.setSubTitle(QCoreApplication.translate("Wizard", u"Please select all the game installations you want to use with OneLauncher. The game paths can be dragged and droped to set their priority. The first item will be the main game instance.", None))
        self.lotroLabel.setText(QCoreApplication.translate("Wizard", u"Lord of The Rings Online", None))

        __sortingEnabled = self.lotroListWidget.isSortingEnabled()
        self.lotroListWidget.setSortingEnabled(False)
        ___qlistwidgetitem = self.lotroListWidget.item(0)
        ___qlistwidgetitem.setText(QCoreApplication.translate("Wizard", u"Manually add game from filesystem...", None));
        self.lotroListWidget.setSortingEnabled(__sortingEnabled)

        self.ddoLabel.setText(QCoreApplication.translate("Wizard", u"Dungeons and Dragons Online", None))

        __sortingEnabled1 = self.ddoListWidget.isSortingEnabled()
        self.ddoListWidget.setSortingEnabled(False)
        ___qlistwidgetitem1 = self.ddoListWidget.item(0)
        ___qlistwidgetitem1.setText(QCoreApplication.translate("Wizard", u"Manually add game from filesystem...", None));
        self.ddoListWidget.setSortingEnabled(__sortingEnabled1)

        self.finishedWizardPage.setTitle(QCoreApplication.translate("Wizard", u"Setup Finished", None))
        self.finishedWizardPage.setSubTitle(QCoreApplication.translate("Wizard", u"That's it! You can check out the settings menu for lots more to configure and the addon manager for game customizations.", None))
    # retranslateUi

