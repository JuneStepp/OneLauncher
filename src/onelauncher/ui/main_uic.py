# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFormLayout,
    QHBoxLayout, QLabel, QLayout, QLineEdit,
    QSizePolicy, QSpacerItem, QTextBrowser, QToolButton,
    QVBoxLayout, QWidget)

from .custom_widgets import (FramelessQMainWindowWithStylePreview, GameNewsfeedBrowser, NoOddSizesQToolButton)
from .qtdesigner.custom_widgets import QMainWindowWithStylePreview

class Ui_winMain(object):
    def setupUi(self, winMain: FramelessQMainWindowWithStylePreview) -> None:
        if not winMain.objectName():
            winMain.setObjectName(u"winMain")
        winMain.resize(790, 470)
        winMain.setUnifiedTitleAndToolBarOnMac(False)
        self.actionPatch = QAction(winMain)
        self.actionPatch.setObjectName(u"actionPatch")
        self.actionLOTRO = QAction(winMain)
        self.actionLOTRO.setObjectName(u"actionLOTRO")
        self.actionDDO = QAction(winMain)
        self.actionDDO.setObjectName(u"actionDDO")
        self.centralwidget = QWidget(winMain)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_4 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setSpacing(3)
        self.verticalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalLayout_4.setContentsMargins(6, 3, 6, 6)
        self.layoutTopButtons = QHBoxLayout()
        self.layoutTopButtons.setSpacing(2)
        self.layoutTopButtons.setObjectName(u"layoutTopButtons")
        self.layoutTopButtons.setContentsMargins(0, 0, 0, 0)
        self.btnOptions = NoOddSizesQToolButton(self.centralwidget)
        self.btnOptions.setObjectName(u"btnOptions")
        self.btnOptions.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnOptions.setAutoRaise(True)

        self.layoutTopButtons.addWidget(self.btnOptions)

        self.btnAddonManager = NoOddSizesQToolButton(self.centralwidget)
        self.btnAddonManager.setObjectName(u"btnAddonManager")
        self.btnAddonManager.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnAddonManager.setAutoRaise(True)

        self.layoutTopButtons.addWidget(self.btnAddonManager)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.layoutTopButtons.addItem(self.horizontalSpacer)

        self.btnAbout = NoOddSizesQToolButton(self.centralwidget)
        self.btnAbout.setObjectName(u"btnAbout")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.btnAbout.sizePolicy().hasHeightForWidth())
        self.btnAbout.setSizePolicy(sizePolicy)
        self.btnAbout.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnAbout.setAutoRaise(True)

        self.layoutTopButtons.addWidget(self.btnAbout)

        self.btnMinimize = NoOddSizesQToolButton(self.centralwidget)
        self.btnMinimize.setObjectName(u"btnMinimize")
        self.btnMinimize.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnMinimize.setAutoRaise(True)

        self.layoutTopButtons.addWidget(self.btnMinimize)

        self.btnExit = NoOddSizesQToolButton(self.centralwidget)
        self.btnExit.setObjectName(u"btnExit")
        self.btnExit.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnExit.setAutoRaise(True)

        self.layoutTopButtons.addWidget(self.btnExit)


        self.verticalLayout_4.addLayout(self.layoutTopButtons)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setSpacing(9)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.imgGameBanner = QLabel(self.centralwidget)
        self.imgGameBanner.setObjectName(u"imgGameBanner")
        self.imgGameBanner.setScaledContents(False)
        self.imgGameBanner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout_3.addWidget(self.imgGameBanner)

        self.txtFeed = GameNewsfeedBrowser(self.centralwidget)
        self.txtFeed.setObjectName(u"txtFeed")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy1.setHorizontalStretch(1)
        sizePolicy1.setVerticalStretch(2)
        sizePolicy1.setHeightForWidth(self.txtFeed.sizePolicy().hasHeightForWidth())
        self.txtFeed.setSizePolicy(sizePolicy1)
        self.txtFeed.setOpenExternalLinks(True)
        self.txtFeed.setOpenLinks(True)

        self.verticalLayout_3.addWidget(self.txtFeed)


        self.horizontalLayout_4.addLayout(self.verticalLayout_3)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.widgetLogin = QWidget(self.centralwidget)
        self.widgetLogin.setObjectName(u"widgetLogin")
        self.layoutLogin = QFormLayout(self.widgetLogin)
        self.layoutLogin.setSpacing(0)
        self.layoutLogin.setContentsMargins(0, 0, 0, 0)
        self.layoutLogin.setObjectName(u"layoutLogin")
        self.layoutLogin.setHorizontalSpacing(6)
        self.layoutLogin.setVerticalSpacing(6)
        self.layoutLogin.setContentsMargins(6, -1, -1, -1)
        self.lblWorld = QLabel(self.widgetLogin)
        self.lblWorld.setObjectName(u"lblWorld")

        self.layoutLogin.setWidget(0, QFormLayout.ItemRole.LabelRole, self.lblWorld)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(6)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.cboWorld = QComboBox(self.widgetLogin)
        self.cboWorld.setObjectName(u"cboWorld")

        self.horizontalLayout.addWidget(self.cboWorld)

        self.btnSwitchGame = QToolButton(self.widgetLogin)
        self.btnSwitchGame.setObjectName(u"btnSwitchGame")
        self.btnSwitchGame.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.btnSwitchGame.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.btnSwitchGame.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

        self.horizontalLayout.addWidget(self.btnSwitchGame)


        self.layoutLogin.setLayout(0, QFormLayout.ItemRole.FieldRole, self.horizontalLayout)

        self.lblAccount = QLabel(self.widgetLogin)
        self.lblAccount.setObjectName(u"lblAccount")

        self.layoutLogin.setWidget(1, QFormLayout.ItemRole.LabelRole, self.lblAccount)

        self.cboAccount = QComboBox(self.widgetLogin)
        self.cboAccount.setObjectName(u"cboAccount")
        self.cboAccount.setEditable(True)
        self.cboAccount.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)

        self.layoutLogin.setWidget(1, QFormLayout.ItemRole.FieldRole, self.cboAccount)

        self.lblPassword = QLabel(self.widgetLogin)
        self.lblPassword.setObjectName(u"lblPassword")

        self.layoutLogin.setWidget(2, QFormLayout.ItemRole.LabelRole, self.lblPassword)

        self.txtPassword = QLineEdit(self.widgetLogin)
        self.txtPassword.setObjectName(u"txtPassword")
        self.txtPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.txtPassword.setClearButtonEnabled(True)

        self.layoutLogin.setWidget(2, QFormLayout.ItemRole.FieldRole, self.txtPassword)

        self.btnLogin = QToolButton(self.widgetLogin)
        self.btnLogin.setObjectName(u"btnLogin")
        self.btnLogin.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

        self.layoutLogin.setWidget(5, QFormLayout.ItemRole.LabelRole, self.btnLogin)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        self.verticalLayout.setContentsMargins(6, -1, -1, -1)
        self.chkSaveAccount = QCheckBox(self.widgetLogin)
        self.chkSaveAccount.setObjectName(u"chkSaveAccount")

        self.verticalLayout.addWidget(self.chkSaveAccount, 0, Qt.AlignmentFlag.AlignTop)

        self.chkSavePassword = QCheckBox(self.widgetLogin)
        self.chkSavePassword.setObjectName(u"chkSavePassword")

        self.verticalLayout.addWidget(self.chkSavePassword, 0, Qt.AlignmentFlag.AlignTop)

        self.verticalSpacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)


        self.layoutLogin.setLayout(5, QFormLayout.ItemRole.FieldRole, self.verticalLayout)


        self.verticalLayout_2.addWidget(self.widgetLogin)

        self.txtStatus = QTextBrowser(self.centralwidget)
        self.txtStatus.setObjectName(u"txtStatus")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(1)
        sizePolicy2.setHeightForWidth(self.txtStatus.sizePolicy().hasHeightForWidth())
        self.txtStatus.setSizePolicy(sizePolicy2)
        self.txtStatus.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.txtStatus.setOpenLinks(False)

        self.verticalLayout_2.addWidget(self.txtStatus)


        self.horizontalLayout_4.addLayout(self.verticalLayout_2)


        self.verticalLayout_4.addLayout(self.horizontalLayout_4)

        winMain.setCentralWidget(self.centralwidget)
        QWidget.setTabOrder(self.cboWorld, self.cboAccount)
        QWidget.setTabOrder(self.cboAccount, self.txtPassword)
        QWidget.setTabOrder(self.txtPassword, self.chkSaveAccount)
        QWidget.setTabOrder(self.chkSaveAccount, self.chkSavePassword)
        QWidget.setTabOrder(self.chkSavePassword, self.txtFeed)
        QWidget.setTabOrder(self.txtFeed, self.btnMinimize)
        QWidget.setTabOrder(self.btnMinimize, self.btnSwitchGame)
        QWidget.setTabOrder(self.btnSwitchGame, self.btnOptions)
        QWidget.setTabOrder(self.btnOptions, self.btnExit)
        QWidget.setTabOrder(self.btnExit, self.btnAddonManager)
        QWidget.setTabOrder(self.btnAddonManager, self.btnAbout)
        QWidget.setTabOrder(self.btnAbout, self.txtStatus)

        self.retranslateUi(winMain)

        QMetaObject.connectSlotsByName(winMain)
    # setupUi

    def retranslateUi(self, winMain: FramelessQMainWindowWithStylePreview) -> None:
        self.actionPatch.setText(QCoreApplication.translate("winMain", u"Patch", None))
        self.actionPatch.setIconText(QCoreApplication.translate("winMain", u"Patch", None))
#if QT_CONFIG(tooltip)
        self.actionPatch.setToolTip(QCoreApplication.translate("winMain", u"Patch", None))
#endif // QT_CONFIG(tooltip)
        self.actionLOTRO.setText(QCoreApplication.translate("winMain", u"Lord of the Rings Online", None))
        self.actionDDO.setText(QCoreApplication.translate("winMain", u"Dungeons and Dragons Online", None))
#if QT_CONFIG(tooltip)
        self.btnOptions.setToolTip(QCoreApplication.translate("winMain", u"Settings", None))
#endif // QT_CONFIG(tooltip)
        self.btnOptions.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-lg", None)])
#if QT_CONFIG(tooltip)
        self.btnAddonManager.setToolTip(QCoreApplication.translate("winMain", u"Addon manager", None))
#endif // QT_CONFIG(tooltip)
        self.btnAddonManager.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-lg", None)])
#if QT_CONFIG(tooltip)
        self.btnAbout.setToolTip(QCoreApplication.translate("winMain", u"About", None))
#endif // QT_CONFIG(tooltip)
        self.btnAbout.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-lg", None)])
#if QT_CONFIG(tooltip)
        self.btnMinimize.setToolTip(QCoreApplication.translate("winMain", u"Minimize", None))
#endif // QT_CONFIG(tooltip)
        self.btnMinimize.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-lg", None)])
#if QT_CONFIG(tooltip)
        self.btnExit.setToolTip(QCoreApplication.translate("winMain", u"Exit", None))
#endif // QT_CONFIG(tooltip)
        self.btnExit.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-lg", None)])
#if QT_CONFIG(tooltip)
        self.lblWorld.setToolTip(QCoreApplication.translate("winMain", u"Game server", None))
#endif // QT_CONFIG(tooltip)
        self.lblWorld.setText(QCoreApplication.translate("winMain", u"World", None))
#if QT_CONFIG(tooltip)
        self.cboWorld.setToolTip(QCoreApplication.translate("winMain", u"Select game server", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.btnSwitchGame.setToolTip(QCoreApplication.translate("winMain", u"Switch game", None))
#endif // QT_CONFIG(tooltip)
        self.btnSwitchGame.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"icon-xl", None)])
        self.lblAccount.setText(QCoreApplication.translate("winMain", u"Account", None))
        self.lblPassword.setText(QCoreApplication.translate("winMain", u"Password", None))
#if QT_CONFIG(tooltip)
        self.btnLogin.setToolTip(QCoreApplication.translate("winMain", u"Start your adventure!", None))
#endif // QT_CONFIG(tooltip)
        self.btnLogin.setText(QCoreApplication.translate("winMain", u"Play", None))
        self.btnLogin.setProperty("qssClass", [
            QCoreApplication.translate("winMain", u"text-xl", None),
            QCoreApplication.translate("winMain", u"px-3.5", None),
            QCoreApplication.translate("winMain", u"py-2", None),
            QCoreApplication.translate("winMain", u"m-2", None)])
#if QT_CONFIG(tooltip)
        self.chkSaveAccount.setToolTip(QCoreApplication.translate("winMain", u"Save last used world and account name", None))
#endif // QT_CONFIG(tooltip)
        self.chkSaveAccount.setText(QCoreApplication.translate("winMain", u"Remember account", None))
#if QT_CONFIG(tooltip)
        self.chkSavePassword.setToolTip(QCoreApplication.translate("winMain", u"Save last used password", None))
#endif // QT_CONFIG(tooltip)
        self.chkSavePassword.setText(QCoreApplication.translate("winMain", u"Remember password", None))
        pass
    # retranslateUi

