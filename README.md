# [OneLauncher](https://Github.com/JuneStepp/OneLauncher)

![OneLauncher window examples](https://i.imgur.com/UtCIHSl.png)

[![GitHub release (latest SemVer including pre-releases)](https://img.shields.io/github/v/release/junestepp/onelauncher?include_prereleases)](https://Github.com/JuneStepp/OneLauncher/releases/latest) [![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

An enhanced launcher for both [LOTRO](https://www.lotro.com/) and [DDO](https://www.ddo.com/) with many features including an addons manager for plugins, skins, and music.

## Features

- Multiple accounts support
- Password saving
- Plugins, skins, and music manager
- External scripting support for addons
- Auto WINE setup for Linux
- Multiple clients support
- *more*

## Installation

The easiest way to get OneLauncher is with a [compiled release](https://Github.com/JuneStepp/OneLauncher/releases/latest). It can also be run with Python or Nix.

- [Latest Release](https://Github.com/JuneStepp/OneLauncher/releases/latest)
- [System Requirements](#system-requirements)
- [Running from source code](CONTRIBUTING.md#development-install)

### System Requirements

#### Windows

Windows 10 (1809 or later) or Windows 11 is required. These are what [Qt6 supports](https://doc.qt.io/qt-6/windows.html).

#### Linux

Most people should just need to [install WINE](https://github.com/lutris/docs/blob/master/WineDependencies.md#distribution-specific-instructions). Review the rest of these requirements if you have trouble after that.

- WINE dependencies. See [these commands](https://github.com/lutris/docs/blob/master/WineDependencies.md#distribution-specific-instructions).
- [OS version supported by Qt](https://doc.qt.io/qt-6/linux.html#supported-configurations)
- Either `libxcb-cursor0` or `xcb-cursor0` if using X11.
- `libz`
- A Secret Service backend such as Gnome Keyring or KWallet

## Command Line Usage

All settings can be overridden from the command line. This is especially useful for making custom shortcuts. For example, loading the LOTRO preview client in French could be done with `--game lotro-preview --locale fr`.

```txt
Usage: onelauncher COMMAND [OPTIONS]

Environment variables can also be used. For example, --config-directory can be  
set with ONELAUNCHER_CONFIG_DIRECTORY.

╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ --help -h             Display this message and exit.                         │
│ --install-completion  Install shell completion for this application.         │
│ --version             Display application version.                           │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Parameters ─────────────────────────────────────────────────────────────────╮
│ --game              Which game to load. Can be either a game type or game    │
│                     config ID. [choices: lotro, lotro-preview, ddo,          │
│                     ddo-preview]                                             │
│ --config-directory  Where OneLauncher settings are stored [default:          │
│                     /home/june/.config/onelauncher]                          │
│ --games-directory   Where OneLauncher game specific data is stored [default: │
│                     /home/june/.local/share/onelauncher/games]               │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Program Options ────────────────────────────────────────────────────────────╮
│ --default-locale              Default language for games and UI              │
│ --always-use-default-locale-  Use default language for UI regardless of game │
│   for-ui --no-always-use-def  language                                       │
│   ault-locale-for-ui                                                         │
│ --games-sorting-mode          Order to show games in UI [choices: priority,  │
│                               last-played, alphabetical]                     │
│ --log-verbosity               Minimum log severity that will be shown in the │
│                               console and log file [choices: debug, info,    │
│                               warning, error, critical]                      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Game Options ───────────────────────────────────────────────────────────────╮
│ --game-directory              The game's install directory                   │
│ --locale                      Language used for game                         │
│ --client-type                 Which version of the game client to use        │
│                               [choices: win64, win32, win32-legacy,          │
│                               win32-legacy]                                  │
│ --high-res-enabled            If the high resolution game files should be    │
│   --no-high-res-enabled       used                                           │
│ --standard-game-launcher-fil  Name of the standard game launcher executable. │
│   ename                       Ex. LotroLauncher.exe                          │
│ --patch-client-filename       Name of the dll used for game patching. Ex.    │
│                               patchclient.dll                                │
│ --game-settings-directory     Custom game settings directory. This is where  │
│                               user preferences, screenshots, and addons are  │
│                               stored.                                        │
│ --newsfeed                    URL of the feed (RSS, ATOM, ect) to show in    │
│                               the launcher                                   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Game Account Options ───────────────────────────────────────────────────────╮
│ --username              Login username                                       │
│ --display-name          Name shown instead of account name                   │
│ --last-used-world-name  World last logged into. Will be the default at next  │
│                         login                                                │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Game Addons Options ────────────────────────────────────────────────────────╮
│ --startup-scripts          Python scripts run before game launch. Paths are  │
│   --empty-startup-scripts  relative to the game's documents config directory │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Game WINE Options ──────────────────────────────────────────────────────────╮
│ --builtin-prefix-enabled      If WINE should be automatically managed        │
│   --no-builtin-prefix-enable                                                 │
│   d                                                                          │
│ --user-wine-executable-path   Path to the WINE executable to use when WINE   │
│                               isn't automatically managed                    │
│ --user-prefix-path            Path to the WINE prefix to use when WINE isn't │
│                               automatically managed                          │
│ --wine-debug-level            Value for the WINEDEBUG environment variable   │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## Information For Addon Developers

### Getting Your Addon in OneLauncher

I follow the RSS feed on [LotroInterface](https://lotrointerface.com) and will add any addons that look to be in the correct format. Compendium files are **not** required.
You can open an issue or email me if your addon still needs to be added.

### Archive Format

- Addons must be uploaded as a zip!
- Archive should have a descriptive name (i.e. not "skin" or "plugin")
- It's okay but not recommended if the archive has no root folder, multiple root folders, or includes part of the path to the data folder like "ui/skins" or "Plugins".

### Compendium Files

Compendium files should be placed inside the top-level directory of your addon, and their names follow the format:

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
    <!--Dependencies can be added for any type of addon. The dependency doesn't have to be of the same addon type as what is dependent on it-->
    <Dependencies>
        <dependency>{INTERFACE ID OF DEPENDENCY}</dependency>
        <!--Any amount of dependencies are fine-->
    </Dependencies>
    <!--An addon can request permission to run a Python script at every game launch.-->
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

Patches must follow the same format as the addon that is being patched. The most common issue is leaving out folders farther up the tree from what is changed.

Here is a list of possible issues to keep in mind when making a patch:

Make sure patch…

- Follows the exact same folder structure as the addon being patched.
- Doesn't edit the compendium file of the addon being patched.
- Is installed after what is being patched.
- Has clear name.

### Collections

Collections of addons can be made by listing the addons you would like in the collection as dependencies of your addon. See the [Compendium Files](#compendium-files) section for how to add dependencies to your addon.

### Dependencies

Dependencies will be installed automatically after your addon. See the [Compendium Files](#compendium-files) section for how to add dependencies to your addon. Turbine Utilities uses ID `0`.

### Startup Scripts

Startup scripts are Python scripts that will be run before every game launch. When installing an addon with a startup script, the user will be prompted for permission for the script to run and shown the contents of the script. Addons should anticipate and handle the user not giving permission. See the [Compendium Files](#compendium-files) section for how to add a startup script to your addon.

#### Builtin Variables

These are pre-set variables that you can access in your startup script.

- `__file__`: The string path to your startup script.
- `__game_dir__`: The string path to the current game directory.
- `__game_config_dir__`: The string path to the current game settings folder. This is normally "The Lord of the Rings Online" or "Dungeons and Dragons Online" in the user's documents folder, but it can be configured differently.

## Custom Clients

### OneLauncher Banner Image

Game banner images are displayed above the newsfeed in OneLauncher and are normally expected to be 300x136 pixels. Images following the path `{Game Directory}/{Locale Resources Folder}/banner.png` will replace the default banner for that game and locale. If there is no image for a user's selected locale, the default image will be shown. An example path is `C://Program Files/Standing Stone Games/Lord of The Rings Online/en/banner.png`.

## License

GPLv3+ License. Copyright 2019-2025 - June Stepp.
See the [LICENSE](LICENSE.md) file for details.

The [Font Awesome](https://github.com/FortAwesome/Font-Awesome/blob/master/LICENSE.txt) font is licensed under the [SIL Open Font License](http://scripts.sil.org/OFL).

The [Material Design Icons](https://github.com/Templarian/MaterialDesign/blob/master/LICENSE) font is licensed under the [Apache License Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

The Lord of the Rings Online is a trademark of Middle-earth Enterprises.
Dungeons & Dragons Online is a trademark of Wizards of the Coast LLC.
The Lord of the Rings Online and Dungeons & Dragons Online games and logos are owned by Standing Stone Games LLC. I am not affiliated with Standing Stone Games LLC, Middle-earth Enterprises, or Wizards of the Coast LLC in any way.
