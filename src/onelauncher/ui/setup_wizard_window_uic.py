# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_wizard.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QButtonGroup, QCheckBox,
    QFormLayout, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QListView, QListWidget, QListWidgetItem,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget, QWizard, QWizardPage)

class Ui_setupWizardWindow(object):
    def setupUi(self, setupWizardWindow: QWizard) -> None:
        if not setupWizardWindow.objectName():
            setupWizardWindow.setObjectName(u"setupWizardWindow")
        setupWizardWindow.resize(621, 411)
        self.languageSelectionWizardPage = QWizardPage()
        self.languageSelectionWizardPage.setObjectName(u"languageSelectionWizardPage")
        self.horizontalLayout_2 = QHBoxLayout(self.languageSelectionWizardPage)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.languageSelectionWizardPage)
        self.label.setObjectName(u"label")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.languagesListWidget = QListWidget(self.languageSelectionWizardPage)
        self.languagesListWidget.setObjectName(u"languagesListWidget")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.languagesListWidget.sizePolicy().hasHeightForWidth())
        self.languagesListWidget.setSizePolicy(sizePolicy)
        self.languagesListWidget.setFrameShape(QFrame.Shape.Box)
        self.languagesListWidget.setEditTriggers(QAbstractItemView.EditTrigger.CurrentChanged|QAbstractItemView.EditTrigger.DoubleClicked|QAbstractItemView.EditTrigger.EditKeyPressed|QAbstractItemView.EditTrigger.SelectedClicked)
        self.languagesListWidget.setProperty(u"showDropIndicator", False)
        self.languagesListWidget.setWordWrap(True)
        self.languagesListWidget.setSortingEnabled(True)

        self.verticalLayout.addWidget(self.languagesListWidget)


        self.horizontalLayout_2.addLayout(self.verticalLayout)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout_2.addItem(self.verticalSpacer_2)

        self.formLayout = QFormLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.formLayout.setFormAlignment(Qt.AlignmentFlag.AlignLeading|Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignTop)
        self.formLayout.setContentsMargins(-1, 12, -1, -1)
        self.alwaysUseDefaultLangForUILabel = QLabel(self.languageSelectionWizardPage)
        self.alwaysUseDefaultLangForUILabel.setObjectName(u"alwaysUseDefaultLangForUILabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.alwaysUseDefaultLangForUILabel)

        self.alwaysUseDefaultLangForUICheckBox = QCheckBox(self.languageSelectionWizardPage)
        self.alwaysUseDefaultLangForUICheckBox.setObjectName(u"alwaysUseDefaultLangForUICheckBox")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.alwaysUseDefaultLangForUICheckBox)


        self.horizontalLayout_2.addLayout(self.formLayout)

        setupWizardWindow.setPage(0, self.languageSelectionWizardPage)
        self.gamesSelectionWizardPage = QWizardPage()
        self.gamesSelectionWizardPage.setObjectName(u"gamesSelectionWizardPage")
        self.gamesSelectionPageLayout = QVBoxLayout(self.gamesSelectionWizardPage)
        self.gamesSelectionPageLayout.setObjectName(u"gamesSelectionPageLayout")
        self.gamesListWidget = QListWidget(self.gamesSelectionWizardPage)
        self.gamesListWidget.setObjectName(u"gamesListWidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.gamesListWidget.sizePolicy().hasHeightForWidth())
        self.gamesListWidget.setSizePolicy(sizePolicy1)
        self.gamesListWidget.setDragEnabled(True)
        self.gamesListWidget.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.gamesListWidget.setDefaultDropAction(Qt.DropAction.TargetMoveAction)
        self.gamesListWidget.setAlternatingRowColors(True)
        self.gamesListWidget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.gamesListWidget.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)

        self.gamesSelectionPageLayout.addWidget(self.gamesListWidget)

        self.gamesDiscoveryStatusLabel = QLabel(self.gamesSelectionWizardPage)
        self.gamesDiscoveryStatusLabel.setObjectName(u"gamesDiscoveryStatusLabel")
        self.gamesDiscoveryStatusLabel.setEnabled(True)

        self.gamesSelectionPageLayout.addWidget(self.gamesDiscoveryStatusLabel)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.downPriorityButton = QPushButton(self.gamesSelectionWizardPage)
        self.downPriorityButton.setObjectName(u"downPriorityButton")

        self.horizontalLayout.addWidget(self.downPriorityButton)

        self.upPriorityButton = QPushButton(self.gamesSelectionWizardPage)
        self.upPriorityButton.setObjectName(u"upPriorityButton")

        self.horizontalLayout.addWidget(self.upPriorityButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout.addItem(self.verticalSpacer)

        self.addExistingGameButton = QPushButton(self.gamesSelectionWizardPage)
        self.addExistingGameButton.setObjectName(u"addExistingGameButton")

        self.horizontalLayout.addWidget(self.addExistingGameButton)

        self.installGameButton = QPushButton(self.gamesSelectionWizardPage)
        self.installGameButton.setObjectName(u"installGameButton")

        self.horizontalLayout.addWidget(self.installGameButton)


        self.gamesSelectionPageLayout.addLayout(self.horizontalLayout)

        setupWizardWindow.setPage(1, self.gamesSelectionWizardPage)
        self.dataDeletionWizardPage = QWizardPage()
        self.dataDeletionWizardPage.setObjectName(u"dataDeletionWizardPage")
        self.verticalLayout_2 = QVBoxLayout(self.dataDeletionWizardPage)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.groupBox = QGroupBox(self.dataDeletionWizardPage)
        self.groupBox.setObjectName(u"groupBox")
        self.horizontalLayout_3 = QHBoxLayout(self.groupBox)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.keepDataRadioButton = QRadioButton(self.groupBox)
        self.gamesDataButtonGroup = QButtonGroup(setupWizardWindow)
        self.gamesDataButtonGroup.setObjectName(u"gamesDataButtonGroup")
        self.gamesDataButtonGroup.addButton(self.keepDataRadioButton)
        self.keepDataRadioButton.setObjectName(u"keepDataRadioButton")

        self.horizontalLayout_3.addWidget(self.keepDataRadioButton)

        self.resetDataRadioButton = QRadioButton(self.groupBox)
        self.gamesDataButtonGroup.addButton(self.resetDataRadioButton)
        self.resetDataRadioButton.setObjectName(u"resetDataRadioButton")

        self.horizontalLayout_3.addWidget(self.resetDataRadioButton)


        self.verticalLayout_2.addWidget(self.groupBox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_2.addItem(self.horizontalSpacer)

        self.gamesDeletionStatusListView = QListView(self.dataDeletionWizardPage)
        self.gamesDeletionStatusListView.setObjectName(u"gamesDeletionStatusListView")
        self.gamesDeletionStatusListView.setProperty(u"showDropIndicator", False)
        self.gamesDeletionStatusListView.setAlternatingRowColors(True)
        self.gamesDeletionStatusListView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)

        self.verticalLayout_2.addWidget(self.gamesDeletionStatusListView)

        setupWizardWindow.setPage(2, self.dataDeletionWizardPage)
        self.finishedWizardPage = QWizardPage()
        self.finishedWizardPage.setObjectName(u"finishedWizardPage")
        setupWizardWindow.setPage(3, self.finishedWizardPage)
#if QT_CONFIG(shortcut)
        self.label.setBuddy(self.languagesListWidget)
        self.alwaysUseDefaultLangForUILabel.setBuddy(self.alwaysUseDefaultLangForUICheckBox)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(setupWizardWindow)

        QMetaObject.connectSlotsByName(setupWizardWindow)
    # setupUi

    def retranslateUi(self, setupWizardWindow: QWizard) -> None:
        setupWizardWindow.setWindowTitle(QCoreApplication.translate("setupWizardWindow", u"Setup Wizard", None))
        self.languageSelectionWizardPage.setTitle(QCoreApplication.translate("setupWizardWindow", u"OneLauncher Setup Wizard:", None))
        self.languageSelectionWizardPage.setSubTitle(QCoreApplication.translate("setupWizardWindow", u"This wizard will quickly take you through the steps needed to get up and running with OneLauncher. ", None))
#if QT_CONFIG(tooltip)
        self.label.setToolTip(QCoreApplication.translate("setupWizardWindow", u"The language used for games by default", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("setupWizardWindow", u"Default Language", None))
#if QT_CONFIG(tooltip)
        self.languagesListWidget.setToolTip(QCoreApplication.translate("setupWizardWindow", u"The language used for games by default", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.alwaysUseDefaultLangForUILabel.setToolTip(QCoreApplication.translate("setupWizardWindow", u"Always show OneLauncher interface in default language", None))
#endif // QT_CONFIG(tooltip)
        self.alwaysUseDefaultLangForUILabel.setText(QCoreApplication.translate("setupWizardWindow", u"Always Use Default Language For UI", None))
        self.gamesSelectionWizardPage.setTitle(QCoreApplication.translate("setupWizardWindow", u"Games Selection", None))
        self.gamesSelectionWizardPage.setSubTitle(QCoreApplication.translate("setupWizardWindow", u"Select your game installations. The first one will be the main game instance.", None))
        self.gamesListWidget.setProperty(u"qssClass", [
            QCoreApplication.translate("setupWizardWindow", u"icon-xl", None)])
        self.gamesDiscoveryStatusLabel.setText("")
#if QT_CONFIG(tooltip)
        self.downPriorityButton.setToolTip(QCoreApplication.translate("setupWizardWindow", u"Decrease priority", None))
#endif // QT_CONFIG(tooltip)
        self.downPriorityButton.setText(QCoreApplication.translate("setupWizardWindow", u"\u2193", None))
#if QT_CONFIG(tooltip)
        self.upPriorityButton.setToolTip(QCoreApplication.translate("setupWizardWindow", u"Increase priority", None))
#endif // QT_CONFIG(tooltip)
        self.upPriorityButton.setText(QCoreApplication.translate("setupWizardWindow", u"\u2191", None))
#if QT_CONFIG(tooltip)
        self.addExistingGameButton.setToolTip(QCoreApplication.translate("setupWizardWindow", u"Select an existing game directory from the file browser", None))
#endif // QT_CONFIG(tooltip)
        self.addExistingGameButton.setText(QCoreApplication.translate("setupWizardWindow", u"Add Existing Game", None))
#if QT_CONFIG(tooltip)
        self.installGameButton.setToolTip(QCoreApplication.translate("setupWizardWindow", u"Create a new game installation", None))
#endif // QT_CONFIG(tooltip)
        self.installGameButton.setText(QCoreApplication.translate("setupWizardWindow", u"Install New Game", None))
        self.dataDeletionWizardPage.setTitle(QCoreApplication.translate("setupWizardWindow", u"Existing Games Data", None))
        self.dataDeletionWizardPage.setSubTitle(QCoreApplication.translate("setupWizardWindow", u"Some of your game installations are already registered with OneLauncher. You can choose to have their settings and accounts either kept or reset. Unselected games are always removed.", None))
        self.groupBox.setTitle(QCoreApplication.translate("setupWizardWindow", u"What should happen to existing game data?", None))
        self.keepDataRadioButton.setText(QCoreApplication.translate("setupWizardWindow", u"Keep it", None))
        self.resetDataRadioButton.setText(QCoreApplication.translate("setupWizardWindow", u"Reset it", None))
        self.gamesDeletionStatusListView.setProperty(u"qssClass", [
            QCoreApplication.translate("setupWizardWindow", u"icon-xl", None)])
        self.finishedWizardPage.setTitle(QCoreApplication.translate("setupWizardWindow", u"Setup Finished", None))
        self.finishedWizardPage.setSubTitle(QCoreApplication.translate("setupWizardWindow", u"That's it! You can always check out the settings menu or addons manager for extra customization.", None))
    # retranslateUi

