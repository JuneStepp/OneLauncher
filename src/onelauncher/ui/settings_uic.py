# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QSizePolicy,
    QTabWidget, QToolButton, QWidget)

class Ui_dlgSettings(object):
    def setupUi(self, dlgSettings):
        if not dlgSettings.objectName():
            dlgSettings.setObjectName(u"dlgSettings")
        dlgSettings.setWindowModality(Qt.ApplicationModal)
        dlgSettings.resize(469, 366)
        font = QFont()
        font.setPointSize(12)
        dlgSettings.setFont(font)
        dlgSettings.setModal(True)
        self.showAdvancedSettingsCheckbox = QCheckBox(dlgSettings)
        self.showAdvancedSettingsCheckbox.setObjectName(u"showAdvancedSettingsCheckbox")
        self.showAdvancedSettingsCheckbox.setGeometry(QRect(20, 332, 211, 28))
        self.showAdvancedSettingsCheckbox.setChecked(True)
        self.tabWidget = QTabWidget(dlgSettings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setGeometry(QRect(0, 0, 471, 371))
        self.gameInfoPage = QWidget()
        self.gameInfoPage.setObjectName(u"gameInfoPage")
        self.formLayoutWidget = QWidget(self.gameInfoPage)
        self.formLayoutWidget.setObjectName(u"formLayoutWidget")
        self.formLayoutWidget.setGeometry(QRect(20, 20, 431, 271))
        self.gameInfoFormLayout = QFormLayout(self.formLayoutWidget)
        self.gameInfoFormLayout.setObjectName(u"gameInfoFormLayout")
        self.gameInfoFormLayout.setContentsMargins(0, 0, 0, 0)
        self.gameNameLabel = QLabel(self.formLayoutWidget)
        self.gameNameLabel.setObjectName(u"gameNameLabel")

        self.gameInfoFormLayout.setWidget(0, QFormLayout.LabelRole, self.gameNameLabel)

        self.gameNameLineEdit = QLineEdit(self.formLayoutWidget)
        self.gameNameLineEdit.setObjectName(u"gameNameLineEdit")

        self.gameInfoFormLayout.setWidget(0, QFormLayout.FieldRole, self.gameNameLineEdit)

        self.gameDescriptionLabel = QLabel(self.formLayoutWidget)
        self.gameDescriptionLabel.setObjectName(u"gameDescriptionLabel")

        self.gameInfoFormLayout.setWidget(1, QFormLayout.LabelRole, self.gameDescriptionLabel)

        self.gameDescriptionLineEdit = QLineEdit(self.formLayoutWidget)
        self.gameDescriptionLineEdit.setObjectName(u"gameDescriptionLineEdit")

        self.gameInfoFormLayout.setWidget(1, QFormLayout.FieldRole, self.gameDescriptionLineEdit)

        self.gameNewsfeedLabel = QLabel(self.formLayoutWidget)
        self.gameNewsfeedLabel.setObjectName(u"gameNewsfeedLabel")

        self.gameInfoFormLayout.setWidget(2, QFormLayout.LabelRole, self.gameNewsfeedLabel)

        self.gameNewsfeedLineEdit = QLineEdit(self.formLayoutWidget)
        self.gameNewsfeedLineEdit.setObjectName(u"gameNewsfeedLineEdit")

        self.gameInfoFormLayout.setWidget(2, QFormLayout.FieldRole, self.gameNewsfeedLineEdit)

        self.gameDirLabel = QLabel(self.formLayoutWidget)
        self.gameDirLabel.setObjectName(u"gameDirLabel")
        self.gameDirLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameInfoFormLayout.setWidget(3, QFormLayout.LabelRole, self.gameDirLabel)

        self.gameDirLayout = QHBoxLayout()
        self.gameDirLayout.setObjectName(u"gameDirLayout")
        self.gameDirLineEdit = QLineEdit(self.formLayoutWidget)
        self.gameDirLineEdit.setObjectName(u"gameDirLineEdit")

        self.gameDirLayout.addWidget(self.gameDirLineEdit)

        self.gameDirButton = QToolButton(self.formLayoutWidget)
        self.gameDirButton.setObjectName(u"gameDirButton")

        self.gameDirLayout.addWidget(self.gameDirButton)


        self.gameInfoFormLayout.setLayout(3, QFormLayout.FieldRole, self.gameDirLayout)

        self.browseGameConfigDirButton = QPushButton(self.formLayoutWidget)
        self.browseGameConfigDirButton.setObjectName(u"browseGameConfigDirButton")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseGameConfigDirButton.sizePolicy().hasHeightForWidth())
        self.browseGameConfigDirButton.setSizePolicy(sizePolicy)

        self.gameInfoFormLayout.setWidget(4, QFormLayout.FieldRole, self.browseGameConfigDirButton)

        self.tabWidget.addTab(self.gameInfoPage, "")
        self.gamePage = QWidget()
        self.gamePage.setObjectName(u"gamePage")
        self.formLayoutWidget_3 = QWidget(self.gamePage)
        self.formLayoutWidget_3.setObjectName(u"formLayoutWidget_3")
        self.formLayoutWidget_3.setGeometry(QRect(20, 19, 431, 271))
        self.gameFormLayout = QFormLayout(self.formLayoutWidget_3)
        self.gameFormLayout.setObjectName(u"gameFormLayout")
        self.gameFormLayout.setContentsMargins(0, 0, 0, 0)
        self.gameLanguageLabel = QLabel(self.formLayoutWidget_3)
        self.gameLanguageLabel.setObjectName(u"gameLanguageLabel")
        self.gameLanguageLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameFormLayout.setWidget(0, QFormLayout.LabelRole, self.gameLanguageLabel)

        self.gameLanguageComboBox = QComboBox(self.formLayoutWidget_3)
        self.gameLanguageComboBox.setObjectName(u"gameLanguageComboBox")

        self.gameFormLayout.setWidget(0, QFormLayout.FieldRole, self.gameLanguageComboBox)

        self.highResCheckBox = QCheckBox(self.formLayoutWidget_3)
        self.highResCheckBox.setObjectName(u"highResCheckBox")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Minimum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.highResCheckBox.sizePolicy().hasHeightForWidth())
        self.highResCheckBox.setSizePolicy(sizePolicy1)

        self.gameFormLayout.setWidget(1, QFormLayout.FieldRole, self.highResCheckBox)

        self.clientLabel = QLabel(self.formLayoutWidget_3)
        self.clientLabel.setObjectName(u"clientLabel")
        self.clientLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameFormLayout.setWidget(2, QFormLayout.LabelRole, self.clientLabel)

        self.clientTypeComboBox = QComboBox(self.formLayoutWidget_3)
        self.clientTypeComboBox.setObjectName(u"clientTypeComboBox")

        self.gameFormLayout.setWidget(2, QFormLayout.FieldRole, self.clientTypeComboBox)

        self.standardLauncherLabel = QLabel(self.formLayoutWidget_3)
        self.standardLauncherLabel.setObjectName(u"standardLauncherLabel")
        self.standardLauncherLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameFormLayout.setWidget(3, QFormLayout.LabelRole, self.standardLauncherLabel)

        self.standardLauncherLineEdit = QLineEdit(self.formLayoutWidget_3)
        self.standardLauncherLineEdit.setObjectName(u"standardLauncherLineEdit")

        self.gameFormLayout.setWidget(3, QFormLayout.FieldRole, self.standardLauncherLineEdit)

        self.standardGameLauncherButton = QPushButton(self.formLayoutWidget_3)
        self.standardGameLauncherButton.setObjectName(u"standardGameLauncherButton")
        sizePolicy.setHeightForWidth(self.standardGameLauncherButton.sizePolicy().hasHeightForWidth())
        self.standardGameLauncherButton.setSizePolicy(sizePolicy)

        self.gameFormLayout.setWidget(4, QFormLayout.FieldRole, self.standardGameLauncherButton)

        self.patchClientLabel = QLabel(self.formLayoutWidget_3)
        self.patchClientLabel.setObjectName(u"patchClientLabel")
        self.patchClientLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameFormLayout.setWidget(5, QFormLayout.LabelRole, self.patchClientLabel)

        self.patchClientLineEdit = QLineEdit(self.formLayoutWidget_3)
        self.patchClientLineEdit.setObjectName(u"patchClientLineEdit")

        self.gameFormLayout.setWidget(5, QFormLayout.FieldRole, self.patchClientLineEdit)

        self.highResLabel = QLabel(self.formLayoutWidget_3)
        self.highResLabel.setObjectName(u"highResLabel")
        self.highResLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.gameFormLayout.setWidget(1, QFormLayout.LabelRole, self.highResLabel)

        self.tabWidget.addTab(self.gamePage, "")
        self.winePage = QWidget()
        self.winePage.setObjectName(u"winePage")
        self.formLayoutWidget_5 = QWidget(self.winePage)
        self.formLayoutWidget_5.setObjectName(u"formLayoutWidget_5")
        self.formLayoutWidget_5.setGeometry(QRect(19, 20, 431, 271))
        self.wineFormLayout = QFormLayout(self.formLayoutWidget_5)
        self.wineFormLayout.setObjectName(u"wineFormLayout")
        self.wineFormLayout.setContentsMargins(0, 0, 0, 0)
        self.autoManageWineLabel = QLabel(self.formLayoutWidget_5)
        self.autoManageWineLabel.setObjectName(u"autoManageWineLabel")

        self.wineFormLayout.setWidget(0, QFormLayout.LabelRole, self.autoManageWineLabel)

        self.autoManageWineCheckBox = QCheckBox(self.formLayoutWidget_5)
        self.autoManageWineCheckBox.setObjectName(u"autoManageWineCheckBox")
        sizePolicy1.setHeightForWidth(self.autoManageWineCheckBox.sizePolicy().hasHeightForWidth())
        self.autoManageWineCheckBox.setSizePolicy(sizePolicy1)

        self.wineFormLayout.setWidget(0, QFormLayout.FieldRole, self.autoManageWineCheckBox)

        self.winePrefixLabel = QLabel(self.formLayoutWidget_5)
        self.winePrefixLabel.setObjectName(u"winePrefixLabel")

        self.wineFormLayout.setWidget(1, QFormLayout.LabelRole, self.winePrefixLabel)

        self.winePrefixLineEdit = QLineEdit(self.formLayoutWidget_5)
        self.winePrefixLineEdit.setObjectName(u"winePrefixLineEdit")
        self.winePrefixLineEdit.setDragEnabled(True)

        self.wineFormLayout.setWidget(1, QFormLayout.FieldRole, self.winePrefixLineEdit)

        self.wineExecutableLabel = QLabel(self.formLayoutWidget_5)
        self.wineExecutableLabel.setObjectName(u"wineExecutableLabel")

        self.wineFormLayout.setWidget(2, QFormLayout.LabelRole, self.wineExecutableLabel)

        self.wineExecutableLineEdit = QLineEdit(self.formLayoutWidget_5)
        self.wineExecutableLineEdit.setObjectName(u"wineExecutableLineEdit")
        self.wineExecutableLineEdit.setDragEnabled(True)

        self.wineFormLayout.setWidget(2, QFormLayout.FieldRole, self.wineExecutableLineEdit)

        self.wineDebugLabel = QLabel(self.formLayoutWidget_5)
        self.wineDebugLabel.setObjectName(u"wineDebugLabel")

        self.wineFormLayout.setWidget(3, QFormLayout.LabelRole, self.wineDebugLabel)

        self.wineDebugLineEdit = QLineEdit(self.formLayoutWidget_5)
        self.wineDebugLineEdit.setObjectName(u"wineDebugLineEdit")

        self.wineFormLayout.setWidget(3, QFormLayout.FieldRole, self.wineDebugLineEdit)

        self.tabWidget.addTab(self.winePage, "")
        self.programPage = QWidget()
        self.programPage.setObjectName(u"programPage")
        self.formLayoutWidget_4 = QWidget(self.programPage)
        self.formLayoutWidget_4.setObjectName(u"formLayoutWidget_4")
        self.formLayoutWidget_4.setGeometry(QRect(20, 20, 431, 271))
        self.programFormLayout = QFormLayout(self.formLayoutWidget_4)
        self.programFormLayout.setObjectName(u"programFormLayout")
        self.programFormLayout.setRowWrapPolicy(QFormLayout.WrapLongRows)
        self.programFormLayout.setContentsMargins(0, 0, 0, 0)
        self.defaultLanguageLabel = QLabel(self.formLayoutWidget_4)
        self.defaultLanguageLabel.setObjectName(u"defaultLanguageLabel")
        self.defaultLanguageLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.programFormLayout.setWidget(0, QFormLayout.LabelRole, self.defaultLanguageLabel)

        self.defaultLanguageComboBox = QComboBox(self.formLayoutWidget_4)
        self.defaultLanguageComboBox.setObjectName(u"defaultLanguageComboBox")
        sizePolicy.setHeightForWidth(self.defaultLanguageComboBox.sizePolicy().hasHeightForWidth())
        self.defaultLanguageComboBox.setSizePolicy(sizePolicy)

        self.programFormLayout.setWidget(0, QFormLayout.FieldRole, self.defaultLanguageComboBox)

        self.defaultLanguageForUILabel = QLabel(self.formLayoutWidget_4)
        self.defaultLanguageForUILabel.setObjectName(u"defaultLanguageForUILabel")
        self.defaultLanguageForUILabel.setMaximumSize(QSize(400, 16777215))
        self.defaultLanguageForUILabel.setAlignment(Qt.AlignCenter)
        self.defaultLanguageForUILabel.setWordWrap(True)

        self.programFormLayout.setWidget(1, QFormLayout.LabelRole, self.defaultLanguageForUILabel)

        self.defaultLanguageForUICheckBox = QCheckBox(self.formLayoutWidget_4)
        self.defaultLanguageForUICheckBox.setObjectName(u"defaultLanguageForUICheckBox")
        sizePolicy1.setHeightForWidth(self.defaultLanguageForUICheckBox.sizePolicy().hasHeightForWidth())
        self.defaultLanguageForUICheckBox.setSizePolicy(sizePolicy1)

        self.programFormLayout.setWidget(1, QFormLayout.FieldRole, self.defaultLanguageForUICheckBox)

        self.gamesSortingModeLabel = QLabel(self.formLayoutWidget_4)
        self.gamesSortingModeLabel.setObjectName(u"gamesSortingModeLabel")
        self.gamesSortingModeLabel.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.programFormLayout.setWidget(2, QFormLayout.LabelRole, self.gamesSortingModeLabel)

        self.gamesSortingModeComboBox = QComboBox(self.formLayoutWidget_4)
        self.gamesSortingModeComboBox.setObjectName(u"gamesSortingModeComboBox")
        sizePolicy.setHeightForWidth(self.gamesSortingModeComboBox.sizePolicy().hasHeightForWidth())
        self.gamesSortingModeComboBox.setSizePolicy(sizePolicy)

        self.programFormLayout.setWidget(2, QFormLayout.FieldRole, self.gamesSortingModeComboBox)

        self.gamesManagementButton = QPushButton(self.formLayoutWidget_4)
        self.gamesManagementButton.setObjectName(u"gamesManagementButton")
        sizePolicy.setHeightForWidth(self.gamesManagementButton.sizePolicy().hasHeightForWidth())
        self.gamesManagementButton.setSizePolicy(sizePolicy)

        self.programFormLayout.setWidget(3, QFormLayout.FieldRole, self.gamesManagementButton)

        self.setupWizardButton = QPushButton(self.formLayoutWidget_4)
        self.setupWizardButton.setObjectName(u"setupWizardButton")
        sizePolicy.setHeightForWidth(self.setupWizardButton.sizePolicy().hasHeightForWidth())
        self.setupWizardButton.setSizePolicy(sizePolicy)

        self.programFormLayout.setWidget(4, QFormLayout.FieldRole, self.setupWizardButton)

        self.tabWidget.addTab(self.programPage, "")
        self.settingsButtonBox = QDialogButtonBox(dlgSettings)
        self.settingsButtonBox.setObjectName(u"settingsButtonBox")
        self.settingsButtonBox.setGeometry(QRect(0, 332, 450, 32))
        self.settingsButtonBox.setOrientation(Qt.Horizontal)
        self.settingsButtonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)
        self.tabWidget.raise_()
        self.settingsButtonBox.raise_()
        self.showAdvancedSettingsCheckbox.raise_()

        self.retranslateUi(dlgSettings)
        self.settingsButtonBox.rejected.connect(dlgSettings.reject)

        self.tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(dlgSettings)
    # setupUi

    def retranslateUi(self, dlgSettings):
        dlgSettings.setWindowTitle(QCoreApplication.translate("dlgSettings", u"Settings", None))
#if QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setToolTip(QCoreApplication.translate("dlgSettings", u"<html><head/><body><p>Enable advanced options</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.showAdvancedSettingsCheckbox.setText(QCoreApplication.translate("dlgSettings", u"Advanced Options", None))
        self.gameNameLabel.setText(QCoreApplication.translate("dlgSettings", u"Name", None))
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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.gameInfoPage), QCoreApplication.translate("dlgSettings", u"Game Info", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageLabel.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.gameLanguageLabel.setText(QCoreApplication.translate("dlgSettings", u"Language", None))
#if QT_CONFIG(tooltip)
        self.gameLanguageComboBox.setToolTip("")
#endif // QT_CONFIG(tooltip)
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
#if QT_CONFIG(tooltip)
        self.highResLabel.setToolTip(QCoreApplication.translate("dlgSettings", u"Enable high resolution game files. You may need to patch the game after enabling this", None))
#endif // QT_CONFIG(tooltip)
        self.highResLabel.setText(QCoreApplication.translate("dlgSettings", u"Hi-Res Graphics", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.gamePage), QCoreApplication.translate("dlgSettings", u"Game", None))
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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.winePage), QCoreApplication.translate("dlgSettings", u"Wine", None))
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
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.programPage), QCoreApplication.translate("dlgSettings", u"OneLauncher", None))
    # retranslateUi

