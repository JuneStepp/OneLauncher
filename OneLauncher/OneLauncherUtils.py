# coding=utf-8
###########################################################################
# Support classes for OneLauncher.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2021 June Stepp <contact@JuneStepp.me>
#
# This file is part of OneLauncher
#
# OneLauncher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# OneLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OneLauncher.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import os
import ssl
from codecs import open as uopen
from http.client import HTTPConnection, HTTPSConnection
from pathlib import Path
from urllib.parse import quote
from xml.sax.saxutils import escape as xml_escape

import defusedxml.minidom

import OneLauncher
from OneLauncher import Settings


def string_encode(s):
    return s.encode()


def string_decode(s):
    return s.decode()


def QByteArray2str(s):
    return str(s, encoding="utf8", errors="replace")


sslContext = None


def checkForCertificates(logger, data_folder: Path):
    # Try to locate the server certificates for HTTPS connections
    certfile = data_folder/"certificates/ca_certs.pem"

    if certfile and not os.access(certfile, os.R_OK):
        logger.error(
            "certificate file expected at '%s' but not found!" % certfile)
        certfile = None

    global sslContext
    sslContext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    sslContext.set_ciphers('DEFAULT@SECLEVEL=1')
    if certfile:
        sslContext.verify_mode = ssl.CERT_REQUIRED
        sslContext.load_verify_locations(certfile)
        logger.info("SSL certificate verification enabled!")
    return sslContext


def WebConnection(urlIn):
    if urlIn.upper().find("HTTP://") >= 0:
        url = urlIn[7:].split("/")[0]
        post = urlIn[7:].replace(url, "")
        return HTTPConnection(url), post
    else:
        url = urlIn[8:].split("/")[0]
        post = urlIn[8:].replace(url, "")
        return (
            HTTPSConnection(url, context=sslContext),  # nosec
            post,
        )


def GetText(nodelist):
    return "".join(
        node.data
        for node in nodelist
        if node.nodeType in [node.TEXT_NODE, node.CDATA_SECTION_NODE]
    )


class BaseConfig:
    def __init__(self, configFile: Path):
        self.GLSDataCenterService = ""
        self.gameName = ""
        self.gameDocumentsDir = ""

        try:
            doc = defusedxml.minidom.parse(str(configFile))

            nodes = doc.getElementsByTagName("appSettings")[0].childNodes
            for node in nodes:
                if node.nodeType == node.ELEMENT_NODE:
                    if node.getAttribute("key") == "Launcher.DataCenterService.GLS":
                        self.GLSDataCenterService = node.getAttribute("value")
                    elif node.getAttribute("key") == "DataCenter.GameName":
                        self.gameName = node.getAttribute("value")
                    elif node.getAttribute("key") == "Product.DocumentFolder":
                        self.gameDocumentsDir = Path(
                            node.getAttribute("value"))

            self.isConfigOK = True
        except:
            self.isConfigOK = False


class DetermineGame:
    def __init__(self):
        self.configFile = ""
        self.configFileAlt = ""
        self.iconFile = ""
        self.pngFile = ""
        self.title = ""

    def GetSettings(self, currentGame):
        self.configFileAlt = Path("TurbineLauncher.exe.config")

        self.__test = "(Preview)" if currentGame.endswith(".Test") else ""
        self.iconFile = Path("images/OneLauncherIcon.png")
        if currentGame.startswith("DDO"):
            self.configFile = Path("ddo.launcherconfig")
            self.pngFile = Path("images")/"DDO.png"

            self.title = f"{OneLauncher.__title__} - DDO {self.__test}"
        else:
            self.configFile = Path("lotro.launcherconfig")
            self.pngFile = Path("images/LOTRO.png")

            self.title = f"{OneLauncher.__title__} - LOTRO {self.__test}"


class GLSDataCenter:
    def __init__(self, urlGLSDataCenterService, gameName):
        SM_TEMPLATE = '<?xml version="1.0" encoding="utf-8"?>\
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">\
<soap:Body><GetDatacenters xmlns="http://www.turbine.com/SE/GLS"><game>%s</game>\
</GetDatacenters></soap:Body></soap:Envelope>'

        SoapMessage = SM_TEMPLATE % (gameName)

        try:
            msg = string_encode(SoapMessage)
            webservice, post = WebConnection(urlGLSDataCenterService)

            webservice.putrequest("POST", post)
            webservice.putheader("Content-type", 'text/xml; charset="UTF-8"')
            webservice.putheader("Content-length", "%d" % len(msg))
            webservice.putheader(
                "SOAPAction", "http://www.turbine.com/SE/GLS/GetDatacenters"
            )
            webservice.endheaders()
            webservice.send(msg)

            webresp = webservice.getresponse()

            tempxml = string_decode(webresp.read())

            file_path = Settings.platform_dirs.user_cache_path/"game/GLSDataCenter.config"
            with uopen(file_path, "w", "utf-8") as outfile:
                outfile.write(tempxml)

            if tempxml == "":
                self.loadSuccess = False
            else:
                doc = defusedxml.minidom.parseString(tempxml)

                self.authServer = GetText(
                    doc.getElementsByTagName("AuthServer")[0].childNodes
                )
                self.patchServer = GetText(
                    doc.getElementsByTagName("PatchServer")[0].childNodes
                )
                self.launchConfigServer = GetText(
                    doc.getElementsByTagName("LauncherConfigurationServer")[
                        0].childNodes
                )

                self.worldList = []

                name = ""
                urlChatServer = ""
                urlStatusServer = ""

                for node in doc.getElementsByTagName("World"):
                    for world in node.childNodes:
                        if world.nodeName == "Name":
                            name = world.firstChild.nodeValue
                        elif world.nodeName == "ChatServerUrl":
                            urlChatServer = world.firstChild.nodeValue
                        elif world.nodeName == "StatusServerUrl":
                            urlStatusServer = world.firstChild.nodeValue

                            # Fix for legendary servers always returning nothing for status
                            urlStatusServer = (f"{urlGLSDataCenterService.rsplit('/Service.asmx', maxsplit=1)[0]}/StatusServer.aspx?s="
                                               f"{urlStatusServer.rsplit('StatusServer.aspx?s=', maxsplit=1)[1]}")
                    self.worldList.append(
                        World(name, urlChatServer, urlStatusServer))

                self.loadSuccess = True
        except:
            self.loadSuccess = False


class LanguageConfig:
    def __init__(self, runDir: Path):
        self.langFound = False
        self.langList = []

        language_data_files = runDir.glob("client_local_*.dat")
        if language_data_files:
            self.langFound = True
            for file in language_data_files:
                # remove "client_local_" (13 chars) and ".dat" (4 chars) from filename
                temp = str(file.name)[13:-4]
                if temp == "English":
                    temp = "EN"
                self.langList.append(temp)


class World:
    def __init__(self, name, urlChatServer, urlServerStatus):
        self.name = name
        self.urlChatServer = urlChatServer
        self.urlServerStatus = urlServerStatus
        self.worldAvailable = False
        self.nowServing = ""
        self.loginServer = ""
        self.queueURL = ""

    def CheckWorld(self):
        try:
            webservice, post = WebConnection(self.urlServerStatus)

            webservice.putrequest("GET", post)
            webservice.endheaders()

            webresp = webservice.getresponse()

            tempxml = string_decode(webresp.read())

            file_path = Settings.platform_dirs.user_cache_path/"game/server.config"
            with uopen(file_path, "w", "utf-8") as outfile:
                outfile.write(tempxml)

            if tempxml == "":
                self.worldAvailable = False
            else:
                doc = defusedxml.minidom.parseString(tempxml)

                try:
                    self.nowServing = GetText(
                        doc.getElementsByTagName("nowservingqueuenumber")[
                            0].childNodes
                    )
                except:
                    self.nowServing = ""

                try:
                    self.queueURL = GetText(
                        doc.getElementsByTagName("queueurls")[0].childNodes
                    ).split(";")[0]
                except:
                    self.queueURL = ""

                self.loginServer = GetText(
                    doc.getElementsByTagName("loginservers")[0].childNodes
                ).split(";")[0]

                self.worldAvailable = True
        except:
            self.worldAvailable = False


class WorldQueueConfig:
    def __init__(self, urlConfigServer, gameDir: Path, clientType):
        self.gameClientFilename = ""
        self.gameClientArgTemplate = ""
        self.crashreceiver = ""
        self.DefaultUploadThrottleMbps = ""
        self.bugurl = ""
        self.authserverurl = ""
        self.supporturl = ""
        self.supportserviceurl = ""
        self.glsticketlifetime = ""
        self.newsFeedURL = ""
        self.newsStyleSheetURL = ""
        self.patchProductCode = ""
        self.worldQueueURL = ""
        self.worldQueueParam = ""

        try:
            webservice, post = WebConnection(urlConfigServer)

            webservice.putrequest("GET", post)
            webservice.endheaders()

            webresp = webservice.getresponse()

            tempxml = string_decode(webresp.read())

            file_path = Settings.platform_dirs.user_cache_path/"game/launcher.config"
            with uopen(file_path, "w", "utf-8") as outfile:
                outfile.write(tempxml)

            if tempxml == "":
                self.loadSuccess = False
            else:
                doc = defusedxml.minidom.parseString(tempxml)

                nodes = doc.getElementsByTagName("appSettings")[0].childNodes
                clientFilenameKey = "GameClient." + clientType + ".Filename"
                for node in nodes:
                    if node.nodeType == node.ELEMENT_NODE:
                        if node.getAttribute("key") == clientFilenameKey:
                            self.gameClientFilename = Path(node.getAttribute(
                                "value"))
                        elif node.getAttribute("key") == "GameClient.WIN32.ArgTemplate":
                            self.gameClientArgTemplate = node.getAttribute(
                                "value")
                        elif node.getAttribute("key") == "GameClient.Arg.crashreceiver":
                            self.crashreceiver = node.getAttribute("value")
                        elif (
                            node.getAttribute("key")
                            == "GameClient.Arg.DefaultUploadThrottleMbps"
                        ):
                            self.DefaultUploadThrottleMbps = node.getAttribute(
                                "value")
                        elif node.getAttribute("key") == "GameClient.Arg.bugurl":
                            self.bugurl = node.getAttribute("value")
                        elif node.getAttribute("key") == "GameClient.Arg.authserverurl":
                            self.authserverurl = node.getAttribute("value")
                        elif node.getAttribute("key") == "GameClient.Arg.supporturl":
                            self.supporturl = node.getAttribute("value")
                        elif (
                            node.getAttribute(
                                "key") == "GameClient.Arg.supportserviceurl"
                        ):
                            self.supportserviceurl = node.getAttribute("value")
                        elif (
                            node.getAttribute(
                                "key") == "GameClient.Arg.glsticketlifetime"
                        ):
                            self.glsticketlifetime = node.getAttribute("value")
                        elif node.getAttribute("key") == "Launcher.NewsFeedCSSUrl":
                            self.newsFeedCSSURL = node.getAttribute("value")
                        elif node.getAttribute("key") == "URL.NewsFeed":
                            self.newsFeedURL = node.getAttribute("value")
                        elif node.getAttribute("key") == "URL.NewsStyleSheet":
                            self.newsStyleSheetURL = node.getAttribute("value")
                        elif node.getAttribute("key") == "Patching.ProductCode":
                            self.patchProductCode = node.getAttribute("value")
                        elif node.getAttribute("key") == "WorldQueue.LoginQueue.URL":
                            self.worldQueueURL = node.getAttribute("value")
                        elif (
                            node.getAttribute("key")
                            == "WorldQueue.TakeANumber.Parameters"
                        ):
                            self.worldQueueParam = node.getAttribute("value")

                self.loadSuccess = True

            # check launcher configs in gameDir for local game client override
            tempxml = ""
            filenames = [
                "TurbineLauncher.exe.config",
                "ddo.launcherconfig",
                "lotro.launcherconfig",
            ]
            for filename in filenames:
                filepath = gameDir/filename
                if filepath.exists():
                    with uopen(filepath, "r", "utf-8") as infile:
                        tempxml = infile.read()
                    doc = defusedxml.minidom.parseString(tempxml)
                    nodes = doc.getElementsByTagName(
                        "appSettings")[0].childNodes

                    self.message = ""
                    for node in nodes:
                        if node.nodeType == node.ELEMENT_NODE:
                            if node.getAttribute("key") == "GameClient.WIN32.Filename":
                                self.gameClientFilename = Path(node.getAttribute(
                                    "value"))
                                self.message = (
                                    '<font color="Khaki">'
                                    + filename
                                    + " 32-bit and/or legacy"
                                    " client override activated</font>"
                                )

                            if node.getAttribute("key") == "GameClient.WIN64.Filename":
                                self.gameClientFilename = Path(node.getAttribute(
                                    "value"))
                                self.message = (
                                    '<font color="Khaki">' + filename + " 64-bit client"
                                    " override activated</font>"
                                )

        except:
            self.loadSuccess = False
            raise


class Game:
    def __init__(self, name, description):
        self.name = name
        self.description = description


class AuthenticateUser:
    def __init__(self, urlLoginServer, name, password, game):
        self.authSuccess = False

        SM_TEMPLATE = '<?xml version="1.0" encoding="utf-8"?>\
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" \
xmlns:xsd="http://www.w3.org/2001/XMLSchema" \
xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">\
<soap:Body><LoginAccount xmlns="http://www.turbine.com/SE/GLS"><username>%s</username>\
<password>%s</password><additionalInfo></additionalInfo></LoginAccount></soap:Body></soap:Envelope>'

        SoapMessage = SM_TEMPLATE % (xml_escape(name), xml_escape(password))

        webresp = None

        try:
            msg = string_encode(SoapMessage)
            webservice, post = WebConnection(urlLoginServer)

            webservice.putrequest("POST", post)
            webservice.putheader("Content-type", 'text/xml; charset="UTF-8"')
            webservice.putheader("Content-length", "%d" % len(msg))
            webservice.putheader(
                "SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount"
            )
            webservice.endheaders()
            webservice.send(msg)

            webresp = webservice.getresponse()

            self.gameList = []

            activeAccount = False
            self.ticket = ""

            tempxml = string_decode(webresp.read())

            file_path = Settings.platform_dirs.user_cache_path/"game/GLSAuthServer.config"
            with uopen(file_path, "w", "utf-8") as outfile:
                outfile.write(tempxml)

            if tempxml == "":
                self.messError = "[E08] Server not found - may be down"
            else:
                doc = defusedxml.minidom.parseString(tempxml)

                self.ticket = GetText(
                    doc.getElementsByTagName("Ticket")[0].childNodes)

                for nodes in doc.getElementsByTagName("GameSubscription"):
                    game2 = ""
                    status = ""
                    name = ""
                    desc = ""

                    for node in nodes.childNodes:
                        if node.nodeName == "Game":
                            game2 = GetText(node.childNodes)
                        elif node.nodeName == "Status":
                            status = GetText(node.childNodes)
                        elif node.nodeName == "Name":
                            name = GetText(node.childNodes)
                        elif node.nodeName == "Description":
                            desc = GetText(node.childNodes)

                    if game2 == game:
                        activeAccount = True
                        self.gameList.append(Game(name, desc))

                if activeAccount:
                    self.messError = "No Error"
                    self.authSuccess = True
                else:
                    self.messError = (
                        "[E14] Game account not associated with user account "
                        "- please visit games website and check account details"
                    )

        except ssl.SSLError:
            self.messError = "[E15] SSL Error occurred in HTTPS connection"
        except:
            if webresp and webresp.status == 500:
                self.messError = "[E07] Account details incorrect"
            else:
                self.messError = "[E08] Server not found - may be down (%s)" % (
                    webresp and webresp.status or "N/A"
                )


class JoinWorldQueue:
    def __init__(self, argTemplate, account, ticket, queue, urlIn):
        try:
            webservice, post = WebConnection(urlIn)

            argComplete = (
                argTemplate.replace("{0}", account)
                .replace("{1}", quote(ticket))
                .replace("{2}", quote(queue))
            )

            msg = string_encode(argComplete)
            webservice.putrequest("POST", post)
            webservice.putheader(
                "Content-type", "application/x-www-form-urlencoded")
            webservice.putheader("Content-length", "%d" % len(msg))
            webservice.putheader(
                "SOAPAction", "http://www.turbine.com/SE/GLS/LoginAccount"
            )
            webservice.endheaders()
            webservice.send(msg)

            webresp = webservice.getresponse()

            tempxml = string_decode(webresp.read())

            file_path = Settings.platform_dirs.user_cache_path/"game/WorldQueue.config"
            with uopen(file_path, "w", "utf-8") as outfile:
                outfile.write(tempxml)

            if tempxml == "":
                self.joinSuccess = False
            else:
                doc = defusedxml.minidom.parseString(tempxml)

                if (
                    GetText(doc.getElementsByTagName("HResult")[0].childNodes)
                    == "0x00000000"
                ):
                    self.number = GetText(
                        doc.getElementsByTagName("QueueNumber")[0].childNodes
                    )
                    self.serving = GetText(
                        doc.getElementsByTagName("NowServingNumber")[
                            0].childNodes
                    )

                    self.joinSuccess = True
                else:
                    self.joinSuccess = False
        except:
            self.joinSuccess = False
