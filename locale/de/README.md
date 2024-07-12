# [OneLauncher](https://Github.com/JuneStepp/OneLauncher)

![OneLauncher Fenster Beispiele](https://i.imgur.com/tlWsBoY.png "OneLauncher Fenster Beispiele")

<p align="center"><a href="https://github.com/junestepp/onelauncher/tree/main/locale/de#onelauncher">Deutsch</a> | <span>English</span> | <a href="https://github.com/junestepp/onelauncher/tree/main/locale/fr#onelauncher">Français</a></p>
<p align="center">Distributed on <a href="https://Github.com/JuneStepp/OneLauncher/releases">GitHub</a>, <a href="https://lotrointerface.com/downloads/info1098-OneLauncher-Add-onmanagerandlauncherforLOTROandDDO.html">LotroInterface</a>, and <a href="https://www.nexusmods.com/lotronline/mods/1?tab=description">NexusMods</a>.</p>

---

[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/junestepp/onelauncher?include_prereleases)](https://Github.com/JuneStepp/OneLauncher/releases/latest) [![Weblate project translated](https://img.shields.io/weblate/progress/onelauncher)](https://hosted.weblate.org/projects/onelauncher/) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Ein verbesserter Launcher für [LOTRO](https://www.lotro.com/) und [DDO](https://www.ddo.com/) mit vielen Features, z.B. Add-on Verwaltung für Plugins, Skins, und Musik.

***Version 2.0 ist mit vielen, vielen Änderungen auf dem Weg. Die derzeitige Version ist allerdings stabil und enthält alle wesentlichen Funktionen.***

## Eigenschaften

- Plugins, Skins und Musikmanager
- Unterstützung mehrerer Konten
- Passwort speichern
- Externe Skriptunterstützung für Add-ons
- Auto WINE Setup für Linux
- Unterstützung mehrerer Spielfenster
- *mehr*

• Installation

Der einfachste Weg um OneLauncher zu installieren ist mit einem vorgefertigten Installer. Linux-Benutzer sollten sicherstellen, dass eine aktuelle Version von Wine installiert ist.

- [**Installers**](https://Github.com/JuneStepp/OneLauncher/releases/latest)
- [Wine instructions](https://github.com/lutris/docs/blob/master/WineDependencies.md#distribution-specific-instructions)
- [Running from source code](#development-install)

## Startargumente

- `--game`: Specifies starting game or game type. Accepted values are `LOTRO`, `DDO`, or the UUID of a game. You can find the UUID of a game by showing advanced options in the settings window.
- `--language`: Specifies game client language. Accepted values are IETF language tags such as `de`, `en-US`, or `fr`.

## Development Install

OneLauncher verwendet [Poetry](https://python-poetry.org) für das Abhängigkeitsmanagement. Um alles einzurichten, führen Sie einfach `poetry install` im Wurzelordner des OneLauncher Quellcodes aus.

### Separate Settings Folders for Default and Preview Game Versions

OneLauncher supports custom game settings folders through the `ddo.launcherconfig` and `lotro.launcherconfig` files located in their respective game install folders. Changing the value for `Product.DocumentFolder` will register the new folder with both OneLauncher and the game. Setting different directory names for the normal and preview versions of games allows for completely separate in-game settings and add-ons between them.

## Development Install

OneLauncher uses [Poetry](https://python-poetry.org) for dependency management. To get everything setup, simply run `poetry install` in the root folder of the OneLauncher source code.

Nuitka can't currently cross-compile, but the InstallBuilder installers can be cross-compiled.

`poetry run python compile.py`

### To translate

OneLauncher uses [Weblate](weblate.org) for translations. You can make an account and contribute translations through their site. See the project page [here](https://hosted.weblate.org/projects/onelauncher/).

Nuitka can't currently cross-compile, but the InstallBuilder installers can be
cross-compiled.

`poetry run python compile.py`

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

- Add-ons must be uploaded as a zip!
- Archive should have a descriptive name (i.e. not "skin" or "plugin")
- It's not recommended, but ok if zip has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

### Compendium Files

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

Patches must follow the same format as the add-on that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.

Here is a list of possible issues to keep in mind when making a patch:

Make sure patch…

### Dependencies

Dependencies will be installed automatically after your add-on. See the [Compendium Files](#compendium-files) section for how to add dependencies to your add-on. Turbine Utilities uses ID `0`.

### Startup Scripts

Startup scripts are Python scripts that will be run before every game launch. When installing an add-on with a startup script, the user will be prompted for permission for the script to run and shown the contents of the script. It is likely that users will not give permission for your script to run, so make sure to program in a message for that situation. See the [Compendium Files](#compendium-files) section for how to add a startup script to your add-on.

#### Builtin Variables

These are pre-set variables that you can access in your startup script.

- `__file__`: The string path to your startup script.
- `__game_dir__`: The string path to the current game directory.
- `__game_config_dir__`: The string path to the current game settings folder. This is normally "The Lord of The Rings Online" or "Dungeons and Dragons Online" in the user's documents folder, but it can be configured differently.

## Custom Clients

### OneLauncher Banner Image

### OneLauncher Banner Image
