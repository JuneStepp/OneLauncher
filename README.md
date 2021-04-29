<img src="https://i.imgur.com/tlWsBoY.png" alt="OneLauncher window examples">

OneLauncher is a custom launcher for The Lord of the Rings Online and Dungeons & Dragons Online
for Linux, Windows, and Mac OS X (testers needed) based on PyLotRO by AJackson. PyLotRO
was originally made to allow Linux and Mac players to enjoy LOTRO, but fell
out of relevance once it was no longer needed. This project aims to make a launcher
with new and interesting features that will always be available whether it's for private
servers after the games have shut down, if the main launcher stops working on Linux, or
if people see that it is The OneLauncher to Rule Them All and use it for that reason too.
It is actually mainly being developed as a fun learning experience and to show my
love for these games.

[OneLauncher](https://github.com/JeremyStepp/OneLauncher)
(c) 2019-2021 Jeremy Stepp

Based on [PyLotRO](https://github.com/nwestfal/pylotro)
(C) 2009 AJackson

Based on [LotROLinux](https://web.archive.org/web/20120424132519/http://www.lotrolinux.com/)
(C) 2007-2008 AJackson

Based on [CLI launcher for
LOTRO](https://sny.name/LOTRO/) (C) 2007-2009 SNy

# Features Overview

- Patching and launching of LOTRO and DDO
- Plugins, skins, and music manager
- Multiple accounts support
- Password saving
- External scripting support for add-ons
- Auto optimum WINE setup for Mac and Linux
- Easy game detection

# Basic Usage

Simply download the executable for your operating system from 
[the releases page](https://Github.com/JeremyStepp/OneLauncher/releases) and install it.
If on Linux or Mac make sure WINE is installed, so all dependencies for the version OneLauncher
installs are met.

# Advanced Usage

## Launch Arguments

- `--game`: Specifies starting game. Accepted values are `LOTRO`, `DDO`, `LOTRO.Test`, and `DDO.Test`
- `--language`: Specifies game client language. Accepted values are `EN`, `DE`, and `FR`

## Separate Settings Folders for Default and Preview Game Versions

OneLauncher supports custom game settings folders through the `ddo.launcherconfig` and `lotro.launcherconfig` files located in their respective game install folders. Changing the value for `Product.DocumentFolder` will register the new folder with both OneLauncher and the game. Setting different directory names for the normal and preview versions of games allows for completely separate in-game settings and add-ons between them. The only exception is that add-on startup scripts installed on both versions of the game will run on both versions if enabled for one. 

## Custom WINE Prefix

A custom WINE prefix can be used by changing the WINE prefix path in the advanced section of the WINE settings tab. ESYNC, FSYNC and DXVK will not be automatically enabled on the custom prefix and the shipped version of WINE will not be kept up to date. A different WINE executable can be specified in the settings if that is an issue. The easiest way to enable the built-in prefix again is by re-running the setup wizard. Please don't complain about the games not working if there are only issues with your custom config.

# Development Install

OneLauncher uses [Poetry](https://python-poetry.org) for dependency management. To get everything setup simply run `poetry install --no-root` in the root folder of the OneLauncher source code.

# To run from source

`poetry run ./RunOneLauncher`

Or.

`poetry run python RunOneLauncher`

# To build

This command is needed due to a bug when building with cx-freeze and Poetry

`poetry run python -m pip install --force-reinstall pip setuptools wheel importlib-metadata cx-freeze`

This is the actual build command

`poetry run python setup.py build`

The project can only be built for the os that the build script is run on,
so it has to be built on every target os individually. The installers can be
cross compiled with InstallBuilder though.

# Add-on Manager Info For Developers

## Getting Your Add-on in OneLauncher

I follow the the RSS feed on [LotroInterface](https://lotrointerface.com) and will add any add-ons that look
to be in the correct format. You can open an issue here or email me if you feel
your add-on needs to be added.

## Archive Format

- Add-ons must be uploaded as a zip!
- Zip should have descriptive name (i.e not "skin" or "plugin")
- It's not recommended, but ok if zip has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

## Compendium Files

You don't need to make a compendium file unless you need dependencies to be auto installed or want a startup script to be run. One is auto generated during installation.

Compendium files should be placed inside the top level directory of your add-on and their names follow the format:

`{NAME}.{plugin/skin/music}compendium`
An example is `Example Plugin.plugincompendium`

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
        <!--More descriptors can be added if more plugins are part of the main plugin. This is a representation of the paths to all the .plugin files.-->
    </Descriptors>
    <!--Dependencies can be added for any type of add-on. The dependency doesn't have to be of the same add-on type as what is dependent on it-->
    <Dependencies>
        <dependency>{INTERFACE ID OF DEPENDENCY}</dependency>
        <!--Any amount of dependencies are fine-->
    </Dependencies>
    <!--An add-on can request permission to run a Python script at every game launch.-->
    <StartupScript>{PATH TO PYTHON SCRIPT IN SAME FORMAT AS DESCRIPTORS}</StartupScript>
</{Plugin/Skin/Music}Config>
```

An example is:

```
<?xml version="1.0" ?>
<PluginConfig>
    <Id>314159</Id>
    <Name>Example Plugin</Name>
    <Version>4.0.4</Version>
    <Author>Jeremy Stepp</Author>
    <InfoUrl>http://www.lotrointerface.com/downloads/info314159</InfoUrl>
    <DownloadUrl>http://www.lotrointerface.com/downloads/download314159</DownloadUrl>
    <Descriptors>
        <descriptor>JeremyStepp\Example.plugin</descriptor>
        <descriptor>JeremyStepp\Another Example.plugin</descriptor>
    </Descriptors>
    <Dependencies>
        <dependency>0</dependency>
        <dependency>367</dependency>
    </Dependencies>
    <StartupScript>JeremyStepp\example.py</StartupScript>
</PluginConfig>
```

## Patches

Patches must follow the same format as the add-on that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.

Here is a list of possible issues to keep in mind when making a patch:

Make sure patch...

- Follows the exact same folder structure as the add-on being patched.
- Doesn't edit the compendium file of the add-on being patched.
- Is installed after what is being patched.
- Has clear name.

## Collections

Collections of add-ons can be made by listing the add-ons you would like in the collection as dependencies of your add-on. See the [Compendium Files](#Compendium-Files) section for how to add dependencies to your add-on.

## Dependencies

Dependencies will be installed automatically after your add-on. See the [Compendium Files](#Compendium-Files) section for how to add dependencies to your add-on.

## Startup Scripts

Startup scripts are Python scripts that will be run before every game launch. When installing an add-on with a startup script the user will be prompted for permission for the script to run and shown the contents of the script. It is likely that users will not give permission for your script to run, so make sure to program in a message for that situation. See the [Compendium Files](#Compendium-Files) section for how to add a startup script to your add-on.
