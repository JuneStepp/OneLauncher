# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings_window.ui'
##
## Created by: Qt User Interface Compiler version 6.10.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpacerItem,
    QStackedWidget, QTabBar, QToolButton, QVBoxLayout,
    QWidget)

from .custom_widgets import (FixedWordWrapQLabel, FramelessQDialogWithStylePreview, NoOddSizesQToolButton)
from .qtdesigner.custom_widgets import QDialogWithStylePreview

class Ui_settingsWindow(object):
    def setupUi(self, settingsWindow: FramelessQDialogWithStylePreview) -> None:
        if not settingsWindow.objectName():
            settingsWindow.setObjectName(u"settingsWindow")
        settingsWindow.setWindowModality(Qt.WindowModality.ApplicationModal)
        settingsWindow.resize(469, 366)
        settingsWindow.setModal(True)
        self.actionRunStandardGameLauncherWithPatchingDisabled = QAction(settingsWindow)
        self.actionRunStandardGameLauncherWithPatchingDisabled.setObjectName(u"actionRunStandardGameLauncherWithPatchingDisabled")
        self.verticalLayout = QVBoxLayout(settingsWindow)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabBar = QTabBar(settingsWindow)
        self.tabBar.setObjectName(u"tabBar")

        self.verticalLayout.addWidget(self.tabBar)

        self.stackedWidget = QStackedWidget(settingsWindow)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.pageGameInfo = QWidget()
        self.pageGameInfo.setObjectName(u"pageGameInfo")
        self.formLayout = QFormLayout(self.pageGameInfo)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setContentsMargins(20, 15, 20, 20)
        self.gameNameLabel = QLabel(self.pageGameInfo)
        self.gameNameLabel.setObjectName(u"gameNameLabel")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.gameNameLabel)

        self.gameNameLineEdit = QLineEdit(self.pageGameInfo)
        self.gameNameLineEdit.setObjectName(u"gameNameLineEdit")

        self.formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.gameNameLineEdit)

        self.gameConfigIDLabel = QLabel(self.pageGameInfo)
        self.gameConfigIDLabel.setObjectName(u"gameConfigIDLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.gameConfigIDLabel)

        self.gameConfigIDLineEdit = QLineEdit(self.pageGameInfo)
        self.gameConfigIDLineEdit.setObjectName(u"gameConfigIDLineEdit")
        self.gameConfigIDLineEdit.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.gameConfigIDLineEdit)

        self.gameDescriptionLabel = QLabel(self.pageGameInfo)
        self.gameDescriptionLabel.setObjectName(u"gameDescriptionLabel")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.gameDescriptionLabel)

        self.gameDescriptionLineEdit = QLineEdit(self.pageGameInfo)
        self.gameDescriptionLineEdit.setObjectName(u"gameDescriptionLineEdit")

        self.formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.gameDescriptionLineEdit)

        self.gameNewsfeedLabel = QLabel(self.pageGameInfo)
        self.gameNewsfeedLabel.setObjectName(u"gameNewsfeedLabel")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.gameNewsfeedLabel)

        self.gameNewsfeedLineEdit = QLineEdit(self.pageGameInfo)
        self.gameNewsfeedLineEdit.setObjectName(u"gameNewsfeedLineEdit")

        self.formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.gameNewsfeedLineEdit)

        self.gameDirLabel = QLabel(self.pageGameInfo)
        self.gameDirLabel.setObjectName(u"gameDirLabel")
        self.gameDirLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.gameDirLabel)

        self.gameDirLayout = QHBoxLayout()
        self.gameDirLayout.setObjectName(u"gameDirLayout")
        self.gameDirLineEdit = QLineEdit(self.pageGameInfo)
        self.gameDirLineEdit.setObjectName(u"gameDirLineEdit")

        self.gameDirLayout.addWidget(self.gameDirLineEdit)

        self.browseForGameDirButton = NoOddSizesQToolButton(self.pageGameInfo)
        self.browseForGameDirButton.setObjectName(u"browseForGameDirButton")

        self.gameDirLayout.addWidget(self.browseForGameDirButton)


        self.formLayout.setLayout(4, QFormLayout.ItemRole.FieldRole, self.gameDirLayout)

        self.browseGameConfigDirButton = QPushButton(self.pageGameInfo)
        self.browseGameConfigDirButton.setObjectName(u"browseGameConfigDirButton")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseGameConfigDirButton.sizePolicy().hasHeightForWidth())
        self.browseGameConfigDirButton.setSizePolicy(sizePolicy)

        self.formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.browseGameConfigDirButton)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout.setItem(6, QFormLayout.ItemRole.FieldRole, self.verticalSpacer)

        self.stackedWidget.addWidget(self.pageGameInfo)
        self.pageGame = QWidget()
        self.pageGame.setObjectName(u"pageGame")
        self.formLayout_2 = QFormLayout(self.pageGame)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.formLayout_2.setContentsMargins(20, 15, 20, 20)
        self.gameLanguageLabel = QLabel(self.pageGame)
        self.gameLanguageLabel.setObjectName(u"gameLanguageLabel")
        self.gameLanguageLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.LabelRole, self.gameLanguageLabel)

        self.gameLanguageComboBox = QComboBox(self.pageGame)
        self.gameLanguageComboBox.setObjectName(u"gameLanguageComboBox")

        self.formLayout_2.setWidget(0, QFormLayout.ItemRole.FieldRole, self.gameLanguageComboBox)

        self.highResLabel = QLabel(self.pageGame)
        self.highResLabel.setObjectName(u"highResLabel")
        self.highResLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.LabelRole, self.highResLabel)

        self.highResCheckBox = QCheckBox(self.pageGame)
        self.highResCheckBox.setObjectName(u"highResCheckBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.highResCheckBox.sizePolicy().hasHeightForWidth())
        self.highResCheckBox.setSizePolicy(sizePolicy1)

        self.formLayout_2.setWidget(1, QFormLayout.ItemRole.FieldRole, self.highResCheckBox)

        self.clientLabel = QLabel(self.pageGame)
        self.clientLabel.setObjectName(u"clientLabel")
        self.clientLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.LabelRole, self.clientLabel)

        self.clientTypeComboBox = QComboBox(self.pageGame)
        self.clientTypeComboBox.setObjectName(u"clientTypeComboBox")

        self.formLayout_2.setWidget(2, QFormLayout.ItemRole.FieldRole, self.clientTypeComboBox)

        self.standardLauncherLabel = QLabel(self.pageGame)
        self.standardLauncherLabel.setObjectName(u"standardLauncherLabel")
        self.standardLauncherLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.LabelRole, self.standardLauncherLabel)

        self.standardLauncherLineEdit = QLineEdit(self.pageGame)
        self.standardLauncherLineEdit.setObjectName(u"standardLauncherLineEdit")

        self.formLayout_2.setWidget(3, QFormLayout.ItemRole.FieldRole, self.standardLauncherLineEdit)

        self.standardGameLauncherButton = QToolButton(self.pageGame)
        self.standardGameLauncherButton.setObjectName(u"standardGameLauncherButton")
        sizePolicy.setHeightForWidth(self.standardGameLauncherButton.sizePolicy().hasHeightForWidth())
        self.standardGameLauncherButton.setSizePolicy(sizePolicy)
        self.standardGameLauncherButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        self.formLayout_2.setWidget(4, QFormLayout.ItemRole.FieldRole, self.standardGameLauncherButton)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_2.setItem(5, QFormLayout.ItemRole.FieldRole, self.verticalSpacer_2)

        self.gameSettingsDirLabel = QLabel(self.pageGame)
        self.gameSettingsDirLabel.setObjectName(u"gameSettingsDirLabel")

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.LabelRole, self.gameSettingsDirLabel)

        self.gameSettingsDirWidget = QWidget(self.pageGame)
        self.gameSettingsDirWidget.setObjectName(u"gameSettingsDirWidget")
        self.gameSettingsDirLayout = QHBoxLayout(self.gameSettingsDirWidget)
        self.gameSettingsDirLayout.setObjectName(u"gameSettingsDirLayout")
        self.gameSettingsDirLayout.setContentsMargins(0, 0, 0, 0)
        self.gameSettingsDirLineEdit = QLineEdit(self.gameSettingsDirWidget)
        self.gameSettingsDirLineEdit.setObjectName(u"gameSettingsDirLineEdit")

        self.gameSettingsDirLayout.addWidget(self.gameSettingsDirLineEdit)

        self.browseForGameSettingsDirButton = NoOddSizesQToolButton(self.gameSettingsDirWidget)
        self.browseForGameSettingsDirButton.setObjectName(u"browseForGameSettingsDirButton")

        self.gameSettingsDirLayout.addWidget(self.browseForGameSettingsDirButton)


        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.FieldRole, self.gameSettingsDirWidget)

        self.stackedWidget.addWidget(self.pageGame)
        self.pageWine = QWidget()
        self.pageWine.setObjectName(u"pageWine")
        self.formLayout_3 = QFormLayout(self.pageWine)
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.formLayout_3.setContentsMargins(20, 15, 20, 20)
        self.autoManageWineLabel = QLabel(self.pageWine)
        self.autoManageWineLabel.setObjectName(u"autoManageWineLabel")

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.LabelRole, self.autoManageWineLabel)

        self.autoManageWineCheckBox = QCheckBox(self.pageWine)
        self.autoManageWineCheckBox.setObjectName(u"autoManageWineCheckBox")
        sizePolicy1.setHeightForWidth(self.autoManageWineCheckBox.sizePolicy().hasHeightForWidth())
        self.autoManageWineCheckBox.setSizePolicy(sizePolicy1)

        self.formLayout_3.setWidget(0, QFormLayout.ItemRole.FieldRole, self.autoManageWineCheckBox)

        self.winePrefixLabel = QLabel(self.pageWine)
        self.winePrefixLabel.setObjectName(u"winePrefixLabel")

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.LabelRole, self.winePrefixLabel)

        self.winePrefixLineEdit = QLineEdit(self.pageWine)
        self.winePrefixLineEdit.setObjectName(u"winePrefixLineEdit")
        self.winePrefixLineEdit.setDragEnabled(True)

        self.formLayout_3.setWidget(1, QFormLayout.ItemRole.FieldRole, self.winePrefixLineEdit)

        self.wineExecutableLabel = QLabel(self.pageWine)
        self.wineExecutableLabel.setObjectName(u"wineExecutableLabel")

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.LabelRole, self.wineExecutableLabel)

        self.wineExecutableLineEdit = QLineEdit(self.pageWine)
        self.wineExecutableLineEdit.setObjectName(u"wineExecutableLineEdit")
        self.wineExecutableLineEdit.setDragEnabled(True)

        self.formLayout_3.setWidget(2, QFormLayout.ItemRole.FieldRole, self.wineExecutableLineEdit)

        self.wineDebugLabel = QLabel(self.pageWine)
        self.wineDebugLabel.setObjectName(u"wineDebugLabel")

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.LabelRole, self.wineDebugLabel)

        self.wineDebugLineEdit = QLineEdit(self.pageWine)
        self.wineDebugLineEdit.setObjectName(u"wineDebugLineEdit")

        self.formLayout_3.setWidget(3, QFormLayout.ItemRole.FieldRole, self.wineDebugLineEdit)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_3.setItem(4, QFormLayout.ItemRole.FieldRole, self.verticalSpacer_3)

        self.stackedWidget.addWidget(self.pageWine)
        self.pageProgram = QWidget()
        self.pageProgram.setObjectName(u"pageProgram")
        self.formLayout_4 = QFormLayout(self.pageProgram)
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.formLayout_4.setContentsMargins(20, 15, 20, 20)
        self.defaultLanguageLabel = QLabel(self.pageProgram)
        self.defaultLanguageLabel.setObjectName(u"defaultLanguageLabel")
        self.defaultLanguageLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.LabelRole, self.defaultLanguageLabel)

        self.defaultLanguageComboBox = QComboBox(self.pageProgram)
        self.defaultLanguageComboBox.setObjectName(u"defaultLanguageComboBox")
        sizePolicy.setHeightForWidth(self.defaultLanguageComboBox.sizePolicy().hasHeightForWidth())
        self.defaultLanguageComboBox.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(0, QFormLayout.ItemRole.FieldRole, self.defaultLanguageComboBox)

        self.defaultLanguageForUILabel = FixedWordWrapQLabel(self.pageProgram)
        self.defaultLanguageForUILabel.setObjectName(u"defaultLanguageForUILabel")
        self.defaultLanguageForUILabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.defaultLanguageForUILabel.setWordWrap(True)

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.LabelRole, self.defaultLanguageForUILabel)

        self.defaultLanguageForUICheckBox = QCheckBox(self.pageProgram)
        self.defaultLanguageForUICheckBox.setObjectName(u"defaultLanguageForUICheckBox")
        sizePolicy1.setHeightForWidth(self.defaultLanguageForUICheckBox.sizePolicy().hasHeightForWidth())
        self.defaultLanguageForUICheckBox.setSizePolicy(sizePolicy1)

        self.formLayout_4.setWidget(1, QFormLayout.ItemRole.FieldRole, self.defaultLanguageForUICheckBox)

        self.gamesSortingModeLabel = QLabel(self.pageProgram)
        self.gamesSortingModeLabel.setObjectName(u"gamesSortingModeLabel")
        self.gamesSortingModeLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.LabelRole, self.gamesSortingModeLabel)

        self.gamesSortingModeComboBox = QComboBox(self.pageProgram)
        self.gamesSortingModeComboBox.setObjectName(u"gamesSortingModeComboBox")
        sizePolicy.setHeightForWidth(self.gamesSortingModeComboBox.sizePolicy().hasHeightForWidth())
        self.gamesSortingModeComboBox.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(2, QFormLayout.ItemRole.FieldRole, self.gamesSortingModeComboBox)

        self.closeAfterStartingGameLabel = FixedWordWrapQLabel(self.pageProgram)
        self.closeAfterStartingGameLabel.setObjectName(u"closeAfterStartingGameLabel")
        self.closeAfterStartingGameLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.closeAfterStartingGameLabel.setWordWrap(True)

        self.formLayout_4.setWidget(4, QFormLayout.ItemRole.LabelRole, self.closeAfterStartingGameLabel)

        self.closeAfterStartingGameCheckBox = QCheckBox(self.pageProgram)
        self.closeAfterStartingGameCheckBox.setObjectName(u"closeAfterStartingGameCheckBox")
        sizePolicy1.setHeightForWidth(self.closeAfterStartingGameCheckBox.sizePolicy().hasHeightForWidth())
        self.closeAfterStartingGameCheckBox.setSizePolicy(sizePolicy1)

        self.formLayout_4.setWidget(4, QFormLayout.ItemRole.FieldRole, self.closeAfterStartingGameCheckBox)

        self.gamesManagementButton = QPushButton(self.pageProgram)
        self.gamesManagementButton.setObjectName(u"gamesManagementButton")
        sizePolicy.setHeightForWidth(self.gamesManagementButton.sizePolicy().hasHeightForWidth())
        self.gamesManagementButton.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(5, QFormLayout.ItemRole.FieldRole, self.gamesManagementButton)

        self.setupWizardButton = QPushButton(self.pageProgram)
        self.setupWizardButton.setObjectName(u"setupWizardButton")
        sizePolicy.setHeightForWidth(self.setupWizardButton.sizePolicy().hasHeightForWidth())
        self.setupWizardButton.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(6, QFormLayout.ItemRole.FieldRole, self.setupWizardButton)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_4.setItem(7, QFormLayout.ItemRole.FieldRole, self.verticalSpacer_4)

        self.stackedWidget.addWidget(self.pageProgram)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.showAdvancedSettingsCheckbox = QCheckBox(settingsWindow)
        self.showAdvancedSettingsCheckbox.setObjectName(u"showAdvancedSettingsCheckbox")
        self.showAdvancedSettingsCheckbox.setChecked(True)

        self.horizontalLayout.addWidget(self.showAdvancedSettingsCheckbox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.settingsButtonBox = QDialogButtonBox(settingsWindow)
        self.settingsButtonBox.setObjectName(u"settingsButtonBox")
        self.settingsButtonBox.setOrientation(Qt.Orientation.Horizontal)
        self.settingsButtonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.horizontalLayout.addWidget(self.settingsButtonBox)


        self.verticalLayout.addLayout(self.horizontalLayout)

#if QT_CONFIG(shortcut)
        self.gameNameLabel.setBuddy(self.gameNameLineEdit)
        self.gameConfigIDLabel.setBuddy(self.gameConfigIDLineEdit)
        self.gameDescriptionLabel.setBuddy(self.gameDescriptionLineEdit)
        self.gameNewsfeedLabel.setBuddy(self.gameNewsfeedLineEdit)
        self.gameDirLabel.setBuddy(self.gameDirLineEdit)
        self.gameLanguageLabel.setBuddy(self.gameLanguageComboBox)
        self.highResLabel.setBuddy(self.highResCheckBox)
        self.clientLabel.setBuddy(self.clientTypeComboBox)
        self.standardLauncherLabel.setBuddy(self.standardLauncherLineEdit)
        self.gameSettingsDirLabel.setBuddy(self.gameSettingsDirLineEdit)
        self.autoManageWineLabel.setBuddy(self.autoManageWineCheckBox)
        self.winePrefixLabel.setBuddy(self.winePrefixLineEdit)
        self.wineExecutableLabel.setBuddy(self.wineExecutableLineEdit)
        self.wineDebugLabel.setBuddy(self.wineDebugLineEdit)
        self.defaultLanguageLabel.setBuddy(self.defaultLanguageComboBox)
        self.defaultLanguageForUILabel.setBuddy(self.defaultLanguageForUICheckBox)
        self.gamesSortingModeLabel.setBuddy(self.gamesSortingModeComboBox)
#endif // QT_CONFIG(shortcut)

        self.retranslateUi(settingsWindow)
        self.settingsButtonBox.rejected.connect(settingsWindow.reject)

        self.stackedWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(settingsWindow)
    # setupUi

    def retranslateUi(self, settingsWindow: FramelessQDialogWithStylePreview) -> None:
        settingsWindow.setWindowTitle(QCoreApplication.translate("settingsWindow", u"Settings", None))
        self.actionRunStandardGameLauncherWithPatchingDisabled.setText(QCoreApplication.translate("settingsWindow", u"Run with patching disabled", None))
#if QT_CONFIG(tooltip)
        self.actionRunStandardGameLauncherWithPatchingDisabled.setToolTip(QCoreApplication.translate("settingsWindow", u"Run launcher using \"-skiprawdownload\" and \"-disablepatch\" arguments", None))
#endif // QT_CONFIG(tooltip)
        self.gameNameLabel.setText(QCoreApplication.translate("settingsWindow", u"Name", None))
        self.gameConfigIDLabel.setText(QCoreApplication.translate("settingsWindow", u"Config ID", None))
        self.gameDescriptionLabel.setText(QCoreApplication.translate("settingsWindow", u"Description", None))
        self.gameNewsfeedLabel.setText(QCoreApplication.translate("settingsWindow", u"Newsfeed URL", None))
#if QT_CONFIG(tooltip)
        self.gameDirLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Game install directory. There should be a file called patchclient.dll here", None))
#endif // QT_CONFIG(tooltip)
        self.gameDirLabel.setText(QCoreApplication.translate("settingsWindow", u"Install Directory", None))
#if QT_CONFIG(tooltip)
        self.gameDirLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"Game install directory. There should be a file called patchclient.dll here", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.browseForGameDirButton.setToolTip(QCoreApplication.translate("settingsWindow", u"Select game install directory from the file browser", None))
#endif // QT_CONFIG(tooltip)
        self.browseForGameDirButton.setProperty(u"qssClass", [
            QCoreApplication.translate("settingsWindow", u"icon-base", None)])
#if QT_CONFIG(tooltip)
        self.browseGameConfigDirButton.setToolTip(QCoreApplication.translate("settingsWindow", u"Browse OneLauncher config/data directory for this game", None))
#endif // QT_CONFIG(tooltip)
        self.browseGameConfigDirButton.setText(QCoreApplication.translate("settingsWindow", u"Browse Config Directory", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageLabel.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.gameLanguageLabel.setText(QCoreApplication.translate("settingsWindow", u"Language", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageComboBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.highResLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Enable high resolution game files. You may need to patch the game after enabling this", None))
#endif // QT_CONFIG(tooltip)
        self.highResLabel.setText(QCoreApplication.translate("settingsWindow", u"Hi-Res Graphics", None))
#if QT_CONFIG(tooltip)
        self.highResCheckBox.setToolTip(QCoreApplication.translate("settingsWindow", u"Enable high resolution game files. You may need to patch the game after enabling this", None))
#endif // QT_CONFIG(tooltip)
        self.highResCheckBox.setText("")
#if QT_CONFIG(tooltip)
        self.clientLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Game client version to use. 64-bit is the most modern. It does work with WINE", None))
#endif // QT_CONFIG(tooltip)
        self.clientLabel.setText(QCoreApplication.translate("settingsWindow", u"Client Type", None))
#if QT_CONFIG(tooltip)
        self.clientTypeComboBox.setToolTip(QCoreApplication.translate("settingsWindow", u"Game client version to use. 64-bit is the most modern. It does work with WINE", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.standardLauncherLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Standard launcher filename", None))
#endif // QT_CONFIG(tooltip)
        self.standardLauncherLabel.setText(QCoreApplication.translate("settingsWindow", u"Standard Launcher", None))
#if QT_CONFIG(tooltip)
        self.standardLauncherLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"Standard launcher filename", None))
#endif // QT_CONFIG(tooltip)
        self.standardGameLauncherButton.setText(QCoreApplication.translate("settingsWindow", u"Run Standard Game Launcher", None))
#if QT_CONFIG(tooltip)
        self.gameSettingsDirLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"<html><head/><body><p>The folder where user preferences, screenshots, and addons are stored. <span style=\" font-weight:700;\">Changing this does not move your existing files. It also won't take affect when using the official game launcher.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.gameSettingsDirLabel.setText(QCoreApplication.translate("settingsWindow", u"Settings Directory", None))
#if QT_CONFIG(tooltip)
        self.gameSettingsDirLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"<html><head/><body><p>The folder where user preferences, screenshots, and addons are stored. <span style=\" font-weight:700;\">Changing this does not move your existing files. It also won't take affect when using the official game launcher.</span></p></body></html>", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.browseForGameSettingsDirButton.setToolTip(QCoreApplication.translate("settingsWindow", u"Select game settings directory from the file browser", None))
#endif // QT_CONFIG(tooltip)
        self.browseForGameSettingsDirButton.setProperty(u"qssClass", [
            QCoreApplication.translate("settingsWindow", u"icon-base", None)])
        self.autoManageWineLabel.setText(QCoreApplication.translate("settingsWindow", u"Auto Manage Wine", None))
#if QT_CONFIG(tooltip)
        self.winePrefixLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Path to WINE prefix", None))
#endif // QT_CONFIG(tooltip)
        self.winePrefixLabel.setText(QCoreApplication.translate("settingsWindow", u"Wine Prefix", None))
#if QT_CONFIG(tooltip)
        self.winePrefixLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"Path to WINE prefix", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.wineExecutableLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Path to WINE executable", None))
#endif // QT_CONFIG(tooltip)
        self.wineExecutableLabel.setText(QCoreApplication.translate("settingsWindow", u"Wine Executable", None))
#if QT_CONFIG(tooltip)
        self.wineExecutableLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"Path to WINE executable", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.wineDebugLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Value for the WINEDEBUG environment variable", None))
#endif // QT_CONFIG(tooltip)
        self.wineDebugLabel.setText(QCoreApplication.translate("settingsWindow", u"WINEDEBUG", None))
#if QT_CONFIG(tooltip)
        self.wineDebugLineEdit.setToolTip(QCoreApplication.translate("settingsWindow", u"Value for the WINEDEBUG environment variable", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.defaultLanguageLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Default language to use for games", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageLabel.setText(QCoreApplication.translate("settingsWindow", u"Default Language", None))
#if QT_CONFIG(tooltip)
        self.defaultLanguageComboBox.setToolTip(QCoreApplication.translate("settingsWindow", u"Default language to use for games", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.defaultLanguageForUILabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Use the default language for OneLauncher even when the current game is set to a different language", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageForUILabel.setText(QCoreApplication.translate("settingsWindow", u"Always Use Default Language For UI", None))
#if QT_CONFIG(tooltip)
        self.defaultLanguageForUICheckBox.setToolTip(QCoreApplication.translate("settingsWindow", u"Use the default language for OneLauncher even when the current game is set to a different language", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageForUICheckBox.setText("")
        self.gamesSortingModeLabel.setText(QCoreApplication.translate("settingsWindow", u"Games Sorting Mode", None))
#if QT_CONFIG(tooltip)
        self.closeAfterStartingGameLabel.setToolTip(QCoreApplication.translate("settingsWindow", u"Close OneLauncher when a game is started", None))
#endif // QT_CONFIG(tooltip)
        self.closeAfterStartingGameLabel.setText(QCoreApplication.translate("settingsWindow", u"Close After Starting Game", None))
#if QT_CONFIG(tooltip)
        self.closeAfterStartingGameCheckBox.setToolTip(QCoreApplication.translate("settingsWindow", u"Close OneLauncher when a game is started", None))
#endif // QT_CONFIG(tooltip)
        self.gamesManagementButton.setText(QCoreApplication.translate("settingsWindow", u"Manage Games", None))
        self.setupWizardButton.setText(QCoreApplication.translate("settingsWindow", u"Run Setup Wizard", None))
#if QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setToolTip(QCoreApplication.translate("settingsWindow", u"Enable advanced options", None))
#endif // QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setText(QCoreApplication.translate("settingsWindow", u"Advanced Options", None))
    # retranslateUi

