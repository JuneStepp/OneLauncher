# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'addon_manager.ui'
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
from PySide6.QtWidgets import (QAbstractItemView, QAbstractScrollArea, QApplication, QFrame,
    QHBoxLayout, QHeaderView, QLineEdit, QProgressBar,
    QPushButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QTabBar, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget)

from .custom_widgets import NoOddSizesQToolButton
from .qtdesigner.custom_widgets import QWidgetWithStylePreview

class Ui_addonManagerWindow(object):
    def setupUi(self, addonManagerWindow: QWidgetWithStylePreview) -> None:
        if not addonManagerWindow.objectName():
            addonManagerWindow.setObjectName(u"addonManagerWindow")
        addonManagerWindow.resize(720, 400)
        self.actionAddonImport = QAction(addonManagerWindow)
        self.actionAddonImport.setObjectName(u"actionAddonImport")
        self.actionShowOnLotrointerface = QAction(addonManagerWindow)
        self.actionShowOnLotrointerface.setObjectName(u"actionShowOnLotrointerface")
        self.actionShowSelectedOnLotrointerface = QAction(addonManagerWindow)
        self.actionShowSelectedOnLotrointerface.setObjectName(u"actionShowSelectedOnLotrointerface")
        self.actionInstallAddon = QAction(addonManagerWindow)
        self.actionInstallAddon.setObjectName(u"actionInstallAddon")
        self.actionUninstallAddon = QAction(addonManagerWindow)
        self.actionUninstallAddon.setObjectName(u"actionUninstallAddon")
        self.actionShowAddonInFileManager = QAction(addonManagerWindow)
        self.actionShowAddonInFileManager.setObjectName(u"actionShowAddonInFileManager")
        self.actionShowPluginsFolderInFileManager = QAction(addonManagerWindow)
        self.actionShowPluginsFolderInFileManager.setObjectName(u"actionShowPluginsFolderInFileManager")
        self.actionShowSkinsFolderInFileManager = QAction(addonManagerWindow)
        self.actionShowSkinsFolderInFileManager.setObjectName(u"actionShowSkinsFolderInFileManager")
        self.actionShowMusicFolderInFileManager = QAction(addonManagerWindow)
        self.actionShowMusicFolderInFileManager.setObjectName(u"actionShowMusicFolderInFileManager")
        self.actionUpdateSelectedAddons = QAction(addonManagerWindow)
        self.actionUpdateSelectedAddons.setObjectName(u"actionUpdateSelectedAddons")
        self.actionUpdateAddon = QAction(addonManagerWindow)
        self.actionUpdateAddon.setObjectName(u"actionUpdateAddon")
        self.actionEnableStartupScript = QAction(addonManagerWindow)
        self.actionEnableStartupScript.setObjectName(u"actionEnableStartupScript")
        self.actionDisableStartupScript = QAction(addonManagerWindow)
        self.actionDisableStartupScript.setObjectName(u"actionDisableStartupScript")
        self.actionShowSelectedAddonsInFileManager = QAction(addonManagerWindow)
        self.actionShowSelectedAddonsInFileManager.setObjectName(u"actionShowSelectedAddonsInFileManager")
        self.verticalLayout_9 = QVBoxLayout(addonManagerWindow)
        self.verticalLayout_9.setSpacing(0)
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.verticalLayout_9.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setSpacing(9)
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(9, 9, 9, 9)
        self.txtSearchBar = QLineEdit(addonManagerWindow)
        self.txtSearchBar.setObjectName(u"txtSearchBar")
        self.txtSearchBar.setClearButtonEnabled(True)

        self.horizontalLayout_3.addWidget(self.txtSearchBar)

        self.btnAddons = NoOddSizesQToolButton(addonManagerWindow)
        self.btnAddons.setObjectName(u"btnAddons")
        self.btnAddons.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        self.horizontalLayout_3.addWidget(self.btnAddons)


        self.verticalLayout_9.addLayout(self.horizontalLayout_3)

        self.tabBarSource = QTabBar(addonManagerWindow)
        self.tabBarSource.setObjectName(u"tabBarSource")

        self.verticalLayout_9.addWidget(self.tabBarSource)

        self.stackedWidgetSource = QStackedWidget(addonManagerWindow)
        self.stackedWidgetSource.setObjectName(u"stackedWidgetSource")
        self.pageInstalled = QWidget()
        self.pageInstalled.setObjectName(u"pageInstalled")
        self.verticalLayout = QVBoxLayout(self.pageInstalled)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.layoutTabBarInstalled = QHBoxLayout()
        self.layoutTabBarInstalled.setSpacing(6)
        self.layoutTabBarInstalled.setObjectName(u"layoutTabBarInstalled")
        self.tabBarInstalled = QTabBar(self.pageInstalled)
        self.tabBarInstalled.setObjectName(u"tabBarInstalled")

        self.layoutTabBarInstalled.addWidget(self.tabBarInstalled, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignBottom)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutTabBarInstalled.addItem(self.horizontalSpacer)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setSpacing(6)
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(6, 6, 6, 6)
        self.btnUpdateAll = QPushButton(self.pageInstalled)
        self.btnUpdateAll.setObjectName(u"btnUpdateAll")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnUpdateAll.sizePolicy().hasHeightForWidth())
        self.btnUpdateAll.setSizePolicy(sizePolicy)
        self.btnUpdateAll.setAutoDefault(False)

        self.horizontalLayout_6.addWidget(self.btnUpdateAll)

        self.btnCheckForUpdates = NoOddSizesQToolButton(self.pageInstalled)
        self.btnCheckForUpdates.setObjectName(u"btnCheckForUpdates")

        self.horizontalLayout_6.addWidget(self.btnCheckForUpdates)


        self.layoutTabBarInstalled.addLayout(self.horizontalLayout_6)


        self.verticalLayout.addLayout(self.layoutTabBarInstalled)

        self.stackedWidgetInstalled = QStackedWidget(self.pageInstalled)
        self.stackedWidgetInstalled.setObjectName(u"stackedWidgetInstalled")
        self.pagePluginsInstalled = QWidget()
        self.pagePluginsInstalled.setObjectName(u"pagePluginsInstalled")
        self.verticalLayout_3 = QVBoxLayout(self.pagePluginsInstalled)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.widgetWithStylePreview = QWidgetWithStylePreview(self.pagePluginsInstalled)
        self.widgetWithStylePreview.setObjectName(u"widgetWithStylePreview")

        self.verticalLayout_3.addWidget(self.widgetWithStylePreview)

        self.tablePluginsInstalled = QTableWidget(self.pagePluginsInstalled)
        self.tablePluginsInstalled.setObjectName(u"tablePluginsInstalled")
        self.tablePluginsInstalled.setFrameShape(QFrame.Shape.NoFrame)
        self.tablePluginsInstalled.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tablePluginsInstalled.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablePluginsInstalled.setDragEnabled(False)
        self.tablePluginsInstalled.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tablePluginsInstalled.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tablePluginsInstalled.setSortingEnabled(True)
        self.tablePluginsInstalled.setCornerButtonEnabled(True)
        self.tablePluginsInstalled.horizontalHeader().setVisible(True)
        self.tablePluginsInstalled.horizontalHeader().setCascadingSectionResizes(False)
        self.tablePluginsInstalled.horizontalHeader().setStretchLastSection(True)
        self.tablePluginsInstalled.verticalHeader().setVisible(False)

        self.verticalLayout_3.addWidget(self.tablePluginsInstalled)

        self.stackedWidgetInstalled.addWidget(self.pagePluginsInstalled)
        self.pageSkinsInstalled = QWidget()
        self.pageSkinsInstalled.setObjectName(u"pageSkinsInstalled")
        self.verticalLayout_4 = QVBoxLayout(self.pageSkinsInstalled)
        self.verticalLayout_4.setSpacing(0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.tableSkinsInstalled = QTableWidget(self.pageSkinsInstalled)
        self.tableSkinsInstalled.setObjectName(u"tableSkinsInstalled")
        self.tableSkinsInstalled.setFrameShape(QFrame.Shape.NoFrame)
        self.tableSkinsInstalled.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableSkinsInstalled.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableSkinsInstalled.setDragEnabled(False)
        self.tableSkinsInstalled.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableSkinsInstalled.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableSkinsInstalled.setSortingEnabled(True)
        self.tableSkinsInstalled.setCornerButtonEnabled(True)
        self.tableSkinsInstalled.horizontalHeader().setVisible(True)
        self.tableSkinsInstalled.horizontalHeader().setCascadingSectionResizes(False)
        self.tableSkinsInstalled.horizontalHeader().setStretchLastSection(True)
        self.tableSkinsInstalled.verticalHeader().setVisible(False)

        self.verticalLayout_4.addWidget(self.tableSkinsInstalled)

        self.stackedWidgetInstalled.addWidget(self.pageSkinsInstalled)
        self.pageMusicInstalled = QWidget()
        self.pageMusicInstalled.setObjectName(u"pageMusicInstalled")
        self.verticalLayout_2 = QVBoxLayout(self.pageMusicInstalled)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tableMusicInstalled = QTableWidget(self.pageMusicInstalled)
        self.tableMusicInstalled.setObjectName(u"tableMusicInstalled")
        self.tableMusicInstalled.setFrameShape(QFrame.Shape.NoFrame)
        self.tableMusicInstalled.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableMusicInstalled.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableMusicInstalled.setDragEnabled(False)
        self.tableMusicInstalled.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableMusicInstalled.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableMusicInstalled.setSortingEnabled(True)
        self.tableMusicInstalled.setCornerButtonEnabled(True)
        self.tableMusicInstalled.horizontalHeader().setVisible(True)
        self.tableMusicInstalled.horizontalHeader().setCascadingSectionResizes(False)
        self.tableMusicInstalled.horizontalHeader().setStretchLastSection(True)
        self.tableMusicInstalled.verticalHeader().setVisible(False)

        self.verticalLayout_2.addWidget(self.tableMusicInstalled)

        self.stackedWidgetInstalled.addWidget(self.pageMusicInstalled)

        self.verticalLayout.addWidget(self.stackedWidgetInstalled)

        self.stackedWidgetSource.addWidget(self.pageInstalled)
        self.pageRemote = QWidget()
        self.pageRemote.setObjectName(u"pageRemote")
        self.verticalLayout_5 = QVBoxLayout(self.pageRemote)
        self.verticalLayout_5.setSpacing(0)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout_5.setContentsMargins(0, 0, 0, 0)
        self.layoutTabBarRemote = QHBoxLayout()
        self.layoutTabBarRemote.setObjectName(u"layoutTabBarRemote")
        self.tabBarRemote = QTabBar(self.pageRemote)
        self.tabBarRemote.setObjectName(u"tabBarRemote")

        self.layoutTabBarRemote.addWidget(self.tabBarRemote, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignBottom)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutTabBarRemote.addItem(self.horizontalSpacer_4)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalLayout_5.setContentsMargins(6, 6, 6, 6)
        self.btnCheckForUpdates_2 = NoOddSizesQToolButton(self.pageRemote)
        self.btnCheckForUpdates_2.setObjectName(u"btnCheckForUpdates_2")

        self.horizontalLayout_5.addWidget(self.btnCheckForUpdates_2)


        self.layoutTabBarRemote.addLayout(self.horizontalLayout_5)


        self.verticalLayout_5.addLayout(self.layoutTabBarRemote)

        self.stackedWidgetRemote = QStackedWidget(self.pageRemote)
        self.stackedWidgetRemote.setObjectName(u"stackedWidgetRemote")
        self.pagePluginsRemote = QWidget()
        self.pagePluginsRemote.setObjectName(u"pagePluginsRemote")
        self.verticalLayout_7 = QVBoxLayout(self.pagePluginsRemote)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_7.setContentsMargins(0, 0, 0, 0)
        self.tablePlugins = QTableWidget(self.pagePluginsRemote)
        self.tablePlugins.setObjectName(u"tablePlugins")
        self.tablePlugins.setFrameShape(QFrame.Shape.NoFrame)
        self.tablePlugins.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tablePlugins.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tablePlugins.setDragEnabled(False)
        self.tablePlugins.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tablePlugins.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tablePlugins.setSortingEnabled(True)
        self.tablePlugins.setCornerButtonEnabled(True)
        self.tablePlugins.horizontalHeader().setVisible(True)
        self.tablePlugins.horizontalHeader().setCascadingSectionResizes(False)
        self.tablePlugins.horizontalHeader().setStretchLastSection(True)
        self.tablePlugins.verticalHeader().setVisible(False)

        self.verticalLayout_7.addWidget(self.tablePlugins)

        self.stackedWidgetRemote.addWidget(self.pagePluginsRemote)
        self.pageSkinsRemote = QWidget()
        self.pageSkinsRemote.setObjectName(u"pageSkinsRemote")
        self.verticalLayout_8 = QVBoxLayout(self.pageSkinsRemote)
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(0, 0, 0, 0)
        self.tableSkins = QTableWidget(self.pageSkinsRemote)
        self.tableSkins.setObjectName(u"tableSkins")
        self.tableSkins.setFrameShape(QFrame.Shape.NoFrame)
        self.tableSkins.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableSkins.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableSkins.setDragEnabled(False)
        self.tableSkins.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableSkins.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableSkins.setSortingEnabled(True)
        self.tableSkins.setCornerButtonEnabled(True)
        self.tableSkins.horizontalHeader().setVisible(True)
        self.tableSkins.horizontalHeader().setCascadingSectionResizes(False)
        self.tableSkins.horizontalHeader().setStretchLastSection(True)
        self.tableSkins.verticalHeader().setVisible(False)

        self.verticalLayout_8.addWidget(self.tableSkins)

        self.stackedWidgetRemote.addWidget(self.pageSkinsRemote)
        self.pageMusicRemote = QWidget()
        self.pageMusicRemote.setObjectName(u"pageMusicRemote")
        self.verticalLayout_6 = QVBoxLayout(self.pageMusicRemote)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.verticalLayout_6.setContentsMargins(0, 0, 0, 0)
        self.tableMusic = QTableWidget(self.pageMusicRemote)
        self.tableMusic.setObjectName(u"tableMusic")
        self.tableMusic.setFrameShape(QFrame.Shape.NoFrame)
        self.tableMusic.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.tableMusic.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableMusic.setDragEnabled(False)
        self.tableMusic.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.tableMusic.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableMusic.setSortingEnabled(True)
        self.tableMusic.setCornerButtonEnabled(True)
        self.tableMusic.horizontalHeader().setVisible(True)
        self.tableMusic.horizontalHeader().setCascadingSectionResizes(False)
        self.tableMusic.horizontalHeader().setStretchLastSection(True)
        self.tableMusic.verticalHeader().setVisible(False)

        self.verticalLayout_6.addWidget(self.tableMusic)

        self.stackedWidgetRemote.addWidget(self.pageMusicRemote)

        self.verticalLayout_5.addWidget(self.stackedWidgetRemote)

        self.stackedWidgetSource.addWidget(self.pageRemote)

        self.verticalLayout_9.addWidget(self.stackedWidgetSource)

        self.progressBar = QProgressBar(addonManagerWindow)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setTextVisible(False)

        self.verticalLayout_9.addWidget(self.progressBar)

        QWidget.setTabOrder(self.txtSearchBar, self.tablePluginsInstalled)
        QWidget.setTabOrder(self.tablePluginsInstalled, self.tableSkinsInstalled)
        QWidget.setTabOrder(self.tableSkinsInstalled, self.tableMusicInstalled)
        QWidget.setTabOrder(self.tableMusicInstalled, self.tablePlugins)
        QWidget.setTabOrder(self.tablePlugins, self.tableSkins)
        QWidget.setTabOrder(self.tableSkins, self.tableMusic)
        QWidget.setTabOrder(self.tableMusic, self.btnAddons)
        QWidget.setTabOrder(self.btnAddons, self.btnUpdateAll)
        QWidget.setTabOrder(self.btnUpdateAll, self.btnCheckForUpdates)
        QWidget.setTabOrder(self.btnCheckForUpdates, self.btnCheckForUpdates_2)

        self.retranslateUi(addonManagerWindow)

        QMetaObject.connectSlotsByName(addonManagerWindow)
    # setupUi

    def retranslateUi(self, addonManagerWindow: QWidgetWithStylePreview) -> None:
        addonManagerWindow.setWindowTitle(QCoreApplication.translate("addonManagerWindow", u"Addons Manager", None))
        self.actionAddonImport.setText(QCoreApplication.translate("addonManagerWindow", u"Import Addons", None))
#if QT_CONFIG(tooltip)
        self.actionAddonImport.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Import addons from files/archives", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(shortcut)
        self.actionAddonImport.setShortcut(QCoreApplication.translate("addonManagerWindow", u"Ctrl+I", None))
#endif // QT_CONFIG(shortcut)
        self.actionShowOnLotrointerface.setText(QCoreApplication.translate("addonManagerWindow", u"Show on lotrointerface.com", None))
        self.actionShowSelectedOnLotrointerface.setText(QCoreApplication.translate("addonManagerWindow", u"Show selected addons on lotrointerface.com", None))
        self.actionInstallAddon.setText(QCoreApplication.translate("addonManagerWindow", u"Install", None))
        self.actionUninstallAddon.setText(QCoreApplication.translate("addonManagerWindow", u"Uninstall", None))
        self.actionShowAddonInFileManager.setText(QCoreApplication.translate("addonManagerWindow", u"Show in file manager", None))
        self.actionShowPluginsFolderInFileManager.setText(QCoreApplication.translate("addonManagerWindow", u"Show plugins folder in file manager", None))
        self.actionShowSkinsFolderInFileManager.setText(QCoreApplication.translate("addonManagerWindow", u"Show skins folder in file manager", None))
        self.actionShowMusicFolderInFileManager.setText(QCoreApplication.translate("addonManagerWindow", u"Show music folder in file manager", None))
        self.actionUpdateSelectedAddons.setText(QCoreApplication.translate("addonManagerWindow", u"Update selected addons", None))
        self.actionUpdateAddon.setText(QCoreApplication.translate("addonManagerWindow", u"Update", None))
        self.actionEnableStartupScript.setText(QCoreApplication.translate("addonManagerWindow", u"Enable startup script", None))
        self.actionDisableStartupScript.setText(QCoreApplication.translate("addonManagerWindow", u"Disable startup script", None))
        self.actionShowSelectedAddonsInFileManager.setText(QCoreApplication.translate("addonManagerWindow", u"Show selected addons in file manager", None))
#if QT_CONFIG(tooltip)
        self.actionShowSelectedAddonsInFileManager.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Show selected addons in file manager", None))
#endif // QT_CONFIG(tooltip)
        self.txtSearchBar.setPlaceholderText(QCoreApplication.translate("addonManagerWindow", u"Search here", None))
#if QT_CONFIG(tooltip)
        self.btnAddons.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Remove addons", None))
#endif // QT_CONFIG(tooltip)
        self.btnAddons.setProperty(u"qssClass", [
            QCoreApplication.translate("addonManagerWindow", u"icon-lg", None),
            QCoreApplication.translate("addonManagerWindow", u"px-2.5", None),
            QCoreApplication.translate("addonManagerWindow", u"py-1", None)])
#if QT_CONFIG(tooltip)
        self.btnUpdateAll.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Update all addons", None))
#endif // QT_CONFIG(tooltip)
        self.btnUpdateAll.setText(QCoreApplication.translate("addonManagerWindow", u"Update All", None))
#if QT_CONFIG(tooltip)
        self.btnCheckForUpdates.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Check for updates", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.btnCheckForUpdates_2.setToolTip(QCoreApplication.translate("addonManagerWindow", u"Check for updates", None))
#endif // QT_CONFIG(tooltip)
        self.progressBar.setProperty(u"qssClass", [
            QCoreApplication.translate("addonManagerWindow", u"max-h-2", None)])
    # retranslateUi

