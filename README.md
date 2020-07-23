OneLauncher is a custom launcher for The Lord of the Rings Online and Dungeons & Dragons Online
for Linux, Windows, and Mac OS X based on PyLotRO by AJackson. PyLotRO
was originally made to allow Linux and Mac players to enjoy LOTRO, but fell
out of relevance once it was no longer needed. This project aims to make a launcher
with new and interesting features that will always be available whether it's for private
servers after the games have shut down, if the main launcher stops working on Linux, or
if people see that it is The OneLauncher to Rule Them All and use it for that reason too.
It is actually mainly being developed as a fun learning experience and to show my
love for these games.

[OneLauncher](https://github.com/JeremyStepp/OneLauncher)
(c) 2019-2020 Jeremy Stepp

Based on [PyLotRO](https://github.com/nwestfal/pylotro)
(C) 2009 AJackson

Based on [LotROLinux](https://web.archive.org/web/20120424132519/http://www.lotrolinux.com/)
(C) 2007-2008 AJackson

Based on [CLI launcher for
LOTRO](https://sny.name/LOTRO/) (C) 2007-2009 SNy

# Features Overview

- Patching and launching of LOTRO and DDO
- Plugins, skins, and music manager (Currently only in source)
- Multiple accounts support (Currently only in source)
- Password saving
- Auto optimum WINE setup for Mac and Linux
- Easy game detection

# Basic Use

Simply download the executable for your operating system from 
[the releases page](https://Github.com/JeremyStepp/OneLauncher/releases) and install it.
If on Linux or Mac make sure Wine is installed, so all dependencies for the version OneLauncher
installs are met.

# Development Install

The following items are required to run OneLauncher from source.
It is recommended to use a virtual environment for development and
building like venv, conda, or virtualenv.

- Python 3.7+
- PySide2
- qdarkstyle
- keyring
- defusedxml
- vkbeautify

## Building Dependencies

### All Platforms
- cx-freeze
- VMWare InstallBuilder (For building installer)

### Windows
- PySide2 5.14.1 (can be installed with `pip install PySide2==5.14.1`)
- pywin32

# To run from source

`./RunOneLauncher`

Or.

`python3 RunOneLauncher`

# To build

`python3 setup.py build`

The project can only be built for the os that the build script is run on,
so it has to be built on every target os individually. The installers can be
cross compiled with InstallBuilder though.

# Addon Manager Info For Developers

## Getting your addon in OneLauncher

I follow the the RSS feed on [LotroInterface](https://lotrointerface.com) and will add any addons that look
to be in the correct format. You can open an issue here or email me if you feel
your addon needs to be added.

## Archive Format

- Addons must be uploaded as a zip!
- Zip should have descriptive name (i.e not "skin" or "plugin")
- It's not recommended, but ok if zip has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

## Compendium Files

You don't need to make a compendium file unless you need dependencies to be auto installed. One is auto generated during installation.

Compendium files should be placed inside the top level directory of your addon and their names follow the format:

`{NAME}.{plugin/skin/music}compendium`
An example is `OneLauncher.plugincompendium`

The contents of compendium files follow the format:

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

## Patches

Patches must follow the same format as the addon that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.

Here is a list of possible issues to keep in mind when making a patch:

Make sure patch...

- Follows the exact same folder structure as the addon being patched.
- Doesn't edit the compendium file of the addon being patched.
- Is installed after what is being patched.
- Has clear name.

## Collections

Collections of addons can be made by listing the addons you would like in the collection as dependencies of your addon. See the [Compendium Files](#Compendium-Files) section for how to add dependencies to your addon.
