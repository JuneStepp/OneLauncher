OneLauncher is a custom launcher for The Lord of the Rings Online and Dungeons & Dragons Online
for Linux, Windows, and Mac OS X based on PyLotRO by AJackson. PyLotRO
was originally made to allow Linux and Mac players to enjoy LOTRO, but fell
out of relevance once it was no longer needed. This project aims to make a launcher
with new and interesting features that will always be available whether it's for private
servers after the games have shut down, if the main launcher stops working on Linux, or
if people see that it is The OneLauncher to Rule Them All and use it for that reason too.
It is actually mainly being developed as a fun learning experience and to show my
love for these games.

OneLauncher
(c) 2020 June Stepp

Based on PyLotRO
(C) 2009 AJackson

Based on LotROLinux
(C) 2007-2008 AJackson

Based on CLI launcher for
LOTRO (C) 2007-2009 SNy

# Features Overview

- Patching and launchering of DDO and LOTRO
- Plugins, skins, and music manager (Currently only in source)
- Auto optimum WINE setup for Mac and Linux
- Easy game detection
- Password saving

# Basic Use

Simply download the appropriate executable for your operating system and double click it!
If on Linux or Mac make sure Wine is installed, so all dependencies for the version OneLauncher
installs are met.

# Development Install

The following items are required to run OneLauncher from source.
It is recomended to use a virtual enviroment for development and
building like venv, conda, or virtualenv.

- Python (3.2+)
- PySide2 (Can be installed with pip)
- qdarkstyle (Can be installed with pip)
- pkg_resources (Comes with setuptools. You probably have it, but it can be installed with pip)
- keyring (Can be installed with pip)
- defusedxml (Can be installed with pip)

- PyInstaller (Needed to build. Can be installed with pip.
  Currently [custom development version](https://github.com/JuneStepp/pyinstaller/archive/develop.zip) is needed)
- pywin32-ctypes (Needed for Windows building. Can be installed with pip)

# To run

`./RunOneLauncher`

Or.

`python3 RunOneLauncher`

# To build

`python3 build.py`

The project can only be built for the os that the build script is run on,
so it has to be built on every target os individually. The building output
for Linux can only be run on systems as up to date or more as the system it
is built on, so an old os may want to be built on. The binary for is
also not cross architecture compatible. Wine can be used for Windows builds
though.

# Roadmap

None of this is set in stone, but it gives a basic idea of some of the major
features I plan to implement. Requests, contributions, and critiques, on anything
are always welcome.

- 1.2 -- Add addon manager (plugins, themes, and abc files)
- 1.3 -- Implement extended lua plugin api (More keyboard action interupts, ect)
- 1.4 -- Full game install from OneLauncher (There was more stuff here, but I already did it)

# Addon Manager Info For Developers

## Getting in Addon Manager

I follow the the RSS feed on LotroInterface and will add any addons that look
to be in the correct format. You can open an issue here or email me if you feel
your addon needs to be added.

## Archive Format

- Addons must be upploaded as a zip!
- Zip should have descriptive name (i.e not "skin" or "plugin")
- It's not recomended, but ok if zip has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

## Compendium Files

You don't need to make a compendium file unless you need dependencies to be auto installed. One is auto generated during installation.

Compendium file names follow the format

`{NAME}.{plugin/skin/music}compendium`
An example is `OneLauncher.plugincompendium`

The compendium files follow the format:

```
<?xml version="1.0" ?>
<{Plugin/Skin/Music}Config>
    <Id>{LOTRO INTERFACE ID}</Id>
    <Name>{NAME}</Name>
    <Version>{VERSION}</Version>
    <Author>{AUTHOR}</Author>
    <InfoUrl>http://www.lotrointerface.com/downloads/info{LOTRO INTERFACE ID}</InfoUrl>
    <DownloadUrl>http://www.lotrointerface.com/downloads/download{LOTRO INTERFACE ID}</DownloadUrl>
    <!--Descriptors only needed for plugins-->
    <Descriptors>
        <descriptor>{AUTHOR}\{NAME}.plugin</descriptor>
        <!--More descriptors can be added if more plugins are part of the main plugin-->
    </Descriptors>
    <!--Dependencies can be added for any type of addon. The dependency doesn't have to be of the same addon type as what is dependent on it-->
    <Dependencies>
        <dependency>{INTERFACE ID OF DEPENDENCY}</dependency>
        <!--Any amount of dependencies are fine-->
  </Dependencies>
</{Plugin/Skin/Music}Config>
```

An example is:

```
<?xml version="1.0" ?>
<PluginConfig>
    <Id>684</Id>
    <Name>ChampionFervour</Name>
    <Version>1.1</Version>
    <Author>D.H1cks</Author>
    <InfoUrl>http://www.lotrointerface.com/downloads/info684</InfoUrl>
    <DownloadUrl>http://www.lotrointerface.com/downloads/download684</DownloadUrl>
    <Descriptors>
        <descriptor>DhorPlugins\ChampionFervour.plugin</descriptor>
    </Descriptors>
    <Dependencies>
        <dependency>0</dependency>
        <dependency>367</dependency>
    </Dependencies>
</PluginConfig>
```

## Patches/Addons

Patches/addons must follow the same format as the addon that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.
