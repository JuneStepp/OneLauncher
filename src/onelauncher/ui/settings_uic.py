# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
##
## Created by: Qt User Interface Compiler version 6.7.2
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

from .custom_widgets import FramelessQDialogWithStylePreview
from .qtdesigner.custom_widgets import QDialogWithStylePreview

class Ui_dlgSettings(object):
    def setupUi(self, dlgSettings: FramelessQDialogWithStylePreview) -> None:
        if not dlgSettings.objectName():
            dlgSettings.setObjectName(u"dlgSettings")
        dlgSettings.setWindowModality(Qt.WindowModality.ApplicationModal)
        dlgSettings.resize(469, 366)
        dlgSettings.setModal(True)
        self.actionRunStandardGameLauncherWithPatchingDisabled = QAction(dlgSettings)
        self.actionRunStandardGameLauncherWithPatchingDisabled.setObjectName(u"actionRunStandardGameLauncherWithPatchingDisabled")
        self.verticalLayout = QVBoxLayout(dlgSettings)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.tabBar = QTabBar(dlgSettings)
        self.tabBar.setObjectName(u"tabBar")

        self.verticalLayout.addWidget(self.tabBar)

        self.stackedWidget = QStackedWidget(dlgSettings)
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

        self.gameUUIDLabel = QLabel(self.pageGameInfo)
        self.gameUUIDLabel.setObjectName(u"gameUUIDLabel")

        self.formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.gameUUIDLabel)

        self.gameUUIDLineEdit = QLineEdit(self.pageGameInfo)
        self.gameUUIDLineEdit.setObjectName(u"gameUUIDLineEdit")
        self.gameUUIDLineEdit.setReadOnly(True)

        self.formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.gameUUIDLineEdit)

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

        self.gameDirButton = QToolButton(self.pageGameInfo)
        self.gameDirButton.setObjectName(u"gameDirButton")

        self.gameDirLayout.addWidget(self.gameDirButton)


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

        self.patchClientLabel = QLabel(self.pageGame)
        self.patchClientLabel.setObjectName(u"patchClientLabel")
        self.patchClientLabel.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.LabelRole, self.patchClientLabel)

        self.patchClientLineEdit = QLineEdit(self.pageGame)
        self.patchClientLineEdit.setObjectName(u"patchClientLineEdit")

        self.formLayout_2.setWidget(6, QFormLayout.ItemRole.FieldRole, self.patchClientLineEdit)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_2.setItem(5, QFormLayout.ItemRole.FieldRole, self.verticalSpacer_2)

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

        self.defaultLanguageForUILabel = QLabel(self.pageProgram)
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

        self.gamesManagementButton = QPushButton(self.pageProgram)
        self.gamesManagementButton.setObjectName(u"gamesManagementButton")
        sizePolicy.setHeightForWidth(self.gamesManagementButton.sizePolicy().hasHeightForWidth())
        self.gamesManagementButton.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(3, QFormLayout.ItemRole.FieldRole, self.gamesManagementButton)

        self.setupWizardButton = QPushButton(self.pageProgram)
        self.setupWizardButton.setObjectName(u"setupWizardButton")
        sizePolicy.setHeightForWidth(self.setupWizardButton.sizePolicy().hasHeightForWidth())
        self.setupWizardButton.setSizePolicy(sizePolicy)

        self.formLayout_4.setWidget(4, QFormLayout.ItemRole.FieldRole, self.setupWizardButton)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.formLayout_4.setItem(5, QFormLayout.ItemRole.FieldRole, self.verticalSpacer_4)

        self.stackedWidget.addWidget(self.pageProgram)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(9, 9, 9, 9)
        self.showAdvancedSettingsCheckbox = QCheckBox(dlgSettings)
        self.showAdvancedSettingsCheckbox.setObjectName(u"showAdvancedSettingsCheckbox")
        self.showAdvancedSettingsCheckbox.setChecked(True)

        self.horizontalLayout.addWidget(self.showAdvancedSettingsCheckbox)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.settingsButtonBox = QDialogButtonBox(dlgSettings)
        self.settingsButtonBox.setObjectName(u"settingsButtonBox")
        self.settingsButtonBox.setOrientation(Qt.Orientation.Horizontal)
        self.settingsButtonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Save)

        self.horizontalLayout.addWidget(self.settingsButtonBox)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.retranslateUi(dlgSettings)
        self.settingsButtonBox.rejected.connect(dlgSettings.reject)

        QMetaObject.connectSlotsByName(dlgSettings)
    # setupUi

    def retranslateUi(self, dlgSettings: FramelessQDialogWithStylePreview) -> None:
        dlgSettings.setWindowTitle(QCoreApplication.translate("dlgSettings", u"Settings", None))
        self.actionRunStandardGameLauncherWithPatchingDisabled.setText(QCoreApplication.translate("dlgSettings", u"Run with patching disabled", None))
#if QT_CONFIG(tooltip)
        self.actionRunStandardGameLauncherWithPatchingDisabled.setToolTip(QCoreApplication.translate("dlgSettings", u"Run launcher using \"-skiprawdownload\" and \"-disablepatch\" arguments", None))
#endif // QT_CONFIG(tooltip)
        self.gameNameLabel.setText(QCoreApplication.translate("dlgSettings", u"Name", None))
        self.gameUUIDLabel.setText(QCoreApplication.translate("dlgSettings", u"UUID", None))
        self.gameDescriptionLabel.setText(QCoreApplication.translate("dlgSettings", u"Description", None))
        self.gameNewsfeedLabel.setText(QCoreApplication.translate("dlgSettings", u"Newsfeed URL", None))
#if QT_CONFIG(tooltip)
        self.gameDirLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Game install directory. There should be a file called patchclient.dll here", None))
#endif // QT_CONFIG(tooltip)
        self.gameDirLabel.setText(QCoreApplication.translate("dlgSettings", u"Install Directory", None))
#if QT_CONFIG(tooltip)
        self.gameDirLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Game install directory. There should be a file called patchclient.dll here", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.gameDirButton.setToolTip(QCoreApplication.translate("dlgSettings", u"Select game directory from file system", None))
#endif // QT_CONFIG(tooltip)
        self.gameDirButton.setText(QCoreApplication.translate("dlgSettings", u"...", None))
#if QT_CONFIG(tooltip)
        self.browseGameConfigDirButton.setToolTip(QCoreApplication.translate("dlgSettings", u"Browse OneLauncher config/data directory for this game", None))
#endif // QT_CONFIG(tooltip)
        self.browseGameConfigDirButton.setText(QCoreApplication.translate("dlgSettings", u"Browse Config Directory", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageLabel.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.gameLanguageLabel.setText(QCoreApplication.translate("dlgSettings", u"Language", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageComboBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.highResLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Enable high resolution game files. You may need to patch the game after enabling this", None))
#endif // QT_CONFIG(tooltip)
        self.highResLabel.setText(QCoreApplication.translate("dlgSettings", u"Hi-Res Graphics", None))
#if QT_CONFIG(tooltip)
        self.highResCheckBox.setToolTip(QCoreApplication.translate("dlgSettings", u"Enable high resolution game files. You may need to patch the game after enabling this", None))
#endif // QT_CONFIG(tooltip)
        self.highResCheckBox.setText("")
#if QT_CONFIG(tooltip)
        self.clientLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Game client version to use. 64-bit is the most modern. It does work with WINE", None))
#endif // QT_CONFIG(tooltip)
        self.clientLabel.setText(QCoreApplication.translate("dlgSettings", u"Client Type", None))
#if QT_CONFIG(tooltip)
        self.clientTypeComboBox.setToolTip(QCoreApplication.translate("dlgSettings", u"Game client version to use. 64-bit is the most modern. It does work with WINE", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.standardLauncherLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Standard launcher filename", None))
#endif // QT_CONFIG(tooltip)
        self.standardLauncherLabel.setText(QCoreApplication.translate("dlgSettings", u"Standard Launcher", None))
#if QT_CONFIG(tooltip)
        self.standardLauncherLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Standard launcher filename", None))
#endif // QT_CONFIG(tooltip)
        self.standardGameLauncherButton.setText(QCoreApplication.translate("dlgSettings", u"Run Standard Game Launcher", None))
#if QT_CONFIG(tooltip)
        self.patchClientLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Patch client DLL filename", None))
#endif // QT_CONFIG(tooltip)
        self.patchClientLabel.setText(QCoreApplication.translate("dlgSettings", u"Patch Client DLL", None))
#if QT_CONFIG(tooltip)
        self.patchClientLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Patch client DLL filename", None))
#endif // QT_CONFIG(tooltip)
        self.autoManageWineLabel.setText(QCoreApplication.translate("dlgSettings", u"Auto Manage Wine", None))
#if QT_CONFIG(tooltip)
        self.winePrefixLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Path to WINE prefix", None))
#endif // QT_CONFIG(tooltip)
        self.winePrefixLabel.setText(QCoreApplication.translate("dlgSettings", u"Wine Prefix", None))
#if QT_CONFIG(tooltip)
        self.winePrefixLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Path to WINE prefix", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.wineExecutableLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Path to WINE executable", None))
#endif // QT_CONFIG(tooltip)
        self.wineExecutableLabel.setText(QCoreApplication.translate("dlgSettings", u"Wine Executable", None))
#if QT_CONFIG(tooltip)
        self.wineExecutableLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Path to WINE executable", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.wineDebugLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Value for WINEDEBUG environment variable", None))
#endif // QT_CONFIG(tooltip)
        self.wineDebugLabel.setText(QCoreApplication.translate("dlgSettings", u"WINEDEBUG", None))
#if QT_CONFIG(tooltip)
        self.wineDebugLineEdit.setToolTip(QCoreApplication.translate("dlgSettings", u"Value for WINEDEBUG environment variable", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.defaultLanguageLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Default language to use for games", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageLabel.setText(QCoreApplication.translate("dlgSettings", u"Default Language", None))
#if QT_CONFIG(tooltip)
        self.defaultLanguageComboBox.setToolTip(QCoreApplication.translate("dlgSettings", u"Default language to use for games", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.defaultLanguageForUILabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Use the default language for OneLauncher even when the current game is set to a different language", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageForUILabel.setText(QCoreApplication.translate("dlgSettings", u"Always Use Default Language For UI", None))
#if QT_CONFIG(tooltip)
        self.defaultLanguageForUICheckBox.setToolTip(QCoreApplication.translate("dlgSettings", u"Use the default language for OneLauncher even when the current game is set to a different language", None))
#endif // QT_CONFIG(tooltip)
        self.defaultLanguageForUICheckBox.setText("")
        self.gamesSortingModeLabel.setText(QCoreApplication.translate("dlgSettings", u"Games Sorting Mode", None))
        self.gamesManagementButton.setText(QCoreApplication.translate("dlgSettings", u"Manage Games", None))
        self.setupWizardButton.setText(QCoreApplication.translate("dlgSettings", u"Run Setup Wizard", None))
#if QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>Enable advanced options</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setText(QCoreApplication.translate("dlgSettings", u"Advanced Options", None))
    # retranslateUi

