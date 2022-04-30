# [OneLauncher](https://Github.com/JuneStepp/OneLauncher)

![OneLauncher window examples](https://i.imgur.com/tlWsBoY.png "OneLauncher window examples")

<p align="center"><a href="https://github.com/junestepp/onelauncher/tree/main/locale/de#onelauncher">Deutsch</a> | <span>English</span> | <a href="https://github.com/junestepp/onelauncher/tree/main/locale/fr#onelauncher">Français</a></p>
<p align="center">Distributed on <a href="https://Github.com/JuneStepp/OneLauncher/releases">GitHub</a>, <a href="https://lotrointerface.com/downloads/info1098-OneLauncher-Add-onmanagerandlauncherforLOTROandDDO.html">LotroInterface</a>, and <a href="https://www.nexusmods.com/lotronline/mods/1?tab=description">NexusMods</a>.</p>

---

[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/junestepp/onelauncher?include_prereleases)](https://Github.com/JuneStepp/OneLauncher/releases/latest) [![Weblate project translated](https://img.shields.io/weblate/progress/onelauncher)](https://hosted.weblate.org/projects/onelauncher/) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

An enhanced launcher for both [LOTRO](https://www.lotro.com/) and [DDO](https://www.ddo.com/) with many features including an Add-on manager for plugins, skins, and music.

***Version 2.0 is on the way with many many changes. The current version is stable and has all major features, though.***

## Features Overview

- Plugins, skins, and music manager
- Multiple accounts support
- Password saving
- External scripting support for add-ons
- Auto optimum WINE setup for Mac and Linux
- Easy game detection
- Game patching and launching
- Multiple clients support
- *more*

## Basic Usage

Simply download the executable for your operating system from [the releases page](https://Github.com/JuneStepp/OneLauncher/releases) and install it.
If on Linux or Mac make sure WINE is installed, so all dependencies for the version OneLauncher
installs are met.

## Advanced Usage

### Launch Arguments

- `--game`: Specifies starting game or game type. Accepted values are `LOTRO`, `DDO`, or the UUID of a game. You can find the UUIDs of your games in the games.toml configuration file.
- `--language`: Specifies game client language. Accepted values are IETF language tags such as `de`, `en-US`, or `fr`.

### Separate Settings Folders for Default and Preview Game Versions

OneLauncher supports custom game settings folders through the `ddo.launcherconfig` and `lotro.launcherconfig` files located in their respective game install folders. Changing the value for `Product.DocumentFolder` will register the new folder with both OneLauncher and the game. Setting different directory names for the normal and preview versions of games allows for completely separate in-game settings and add-ons between them.

## Development Install

OneLauncher uses [Poetry](https://python-poetry.org) for dependency management. To get everything setup, simply run `poetry install` in the root folder of the OneLauncher source code.

### To run from source

`poetry run onelauncher`

### To build

The build ends up in `start_onelauncher.dist`.

Nuitka can't currently cross-compile, but the InstallBuilder installers can be
cross-compiled.

`poetry run python compile.py`

### To translate

OneLauncher uses [Weblate](weblate.org) for translations. You can make an account and contribute translations through their site. See the project page [here](https://hosted.weblate.org/projects/onelauncher/).

## Add-on Manager Info For Developers

### Getting Your Add-on in OneLauncher

I follow the RSS feed on [LotroInterface](https://lotrointerface.com) and will add any add-ons that look
to be in the correct format. Compendium files are **not** required.
You can open an issue here or email me if you feel
your add-on needs to be added.

### Archive Format

- Add-ons must be uploaded as a zip!
- Archive should have a descriptive name (i.e. not "skin" or "plugin")
- It's not recommended, but ok if zip has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

### Compendium Files

Compendium files should be placed inside the top-level directory of your add-on, and their names follow the format:

`{NAME}.{plugin/skin/music}compendium`
An example is `Example Plugin.plugincompendium`

The contents of compendium files follow the format:

```xml
<{Plugin/Skin/Music}Config>
    <Id>{LOTRO INTERFACE ID}</Id>
    <Name>{NAME}</Name>
    <Description>{DESCRIPTION}</Description>
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

```xml
<PluginConfig>
    <Id>314159</Id>
    <Name>Example Plugin</Name>
    <Description>Does example things</Description>
    <Version>4.0.4</Version>
    <Author>June Stepp</Author>
    <InfoUrl>http://www.lotrointerface.com/downloads/info314159</InfoUrl>
    <DownloadUrl>http://www.lotrointerface.com/downloads/download314159</DownloadUrl>
    <Descriptors>
        <descriptor>JuneStepp\Example.plugin</descriptor>
        <descriptor>JuneStepp\Another Example.plugin</descriptor>
    </Descriptors>
    <Dependencies>
        <dependency>0</dependency>
        <dependency>367</dependency>
    </Dependencies>
    <StartupScript>JuneStepp\example.py</StartupScript>
</PluginConfig>
```

There is a [vscode extension](https://github.com/lunarwtr/vscode-lotro-api) by @lunarwtr that can lint compendium and other related files. It includes [XML schemas](https://github.com/lunarwtr/vscode-lotro-api/tree/main/xsds) you can manually reference as well.

### Patches

Patches must follow the same format as the add-on that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.

Here is a list of possible issues to keep in mind when making a patch:

Make sure patch…

- Follows the exact same folder structure as the add-on being patched.
- Doesn't edit the compendium file of the add-on being patched.
- Is installed after what is being patched.
- Has clear name.

### Collections

Collections of add-ons can be made by listing the add-ons you would like in the collection as dependencies of your add-on. See the [Compendium Files](#Compendium-Files) section for how to add dependencies to your add-on.

### Dependencies

Dependencies will be installed automatically after your add-on. See the [Compendium Files](#Compendium-Files) section for how to add dependencies to your add-on. Turbine Utilities uses ID `0`.

### Startup Scripts

Startup scripts are Python scripts that will be run before every game launch. When installing an add-on with a startup script, the user will be prompted for permission for the script to run and shown the contents of the script. It is likely that users will not give permission for your script to run, so make sure to program in a message for that situation. See the [Compendium Files](#Compendium-Files) section for how to add a startup script to your add-on.

#### Builtin Variables

These are pre-set variables that you can access in your startup script.

- `__file__`: The string path to your startup script.
- `__game_dir__`: The string path to the current game directory.
- `__game_config_dir__`: The string path to the current game settings folder. This is normally "The Lord of The Rings Online" or "Dungeons and Dragons Online" in the user's documents folder, but it can be configured differently.

## Custom Clients

### OneLauncher Banner Image

Game banner images are displayed above the newsfeed in OneLauncher. All images are scaled to 136 pixels in height keeping aspect ratio and should ideally should be 300x136. Images following the path `{Game Directory}/{Locale Resources Folder}/banner.png` will replace the default image for that game and locale. If there is no image for a user's selected locale, the default image will be shown. An example path is `C://Program Files/Standing Stone Games/Lord of The Rings Online/en/banner.png`.
