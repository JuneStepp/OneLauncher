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
(c) 2019 June Stepp

Based on PyLotRO
(C) 2009 AJackson

Based on LotROLinux
(C) 2007-2008 AJackson

Based on CLI launcher for
LOTRO (C) 2007-2009 SNy

# Basic Use

 Simply download the appropriate executable for your operating system and double click it!

# Development Install

The following items are required to run OneLauncher from source.
It is recomended to use a virtual enviroment for development and
building like venv, conda, or virtualenv.

-   Python (3.2+)
-   qtpy (Can be installed with pip)
-   PyQt5 (Can be installed with pip)
-   qdarkstyle (Can be installed with pip)
-   pkg_resources (Comes with setuptools. You probably have it, but it can be installed with pip)
-   keyring (Can be installed with pip)

-   PyInstaller (Needed to build. Can be installed with pip.
    Currently [custom development version](https://github.com/JuneStepp/pyinstaller/archive/develop.zip) is needed)
-   pywin32-ctypes (Needed for Windows building. Can be installed with pip)

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

-  1.1 -- Fix up setup wizard, have it come up at first start, and add auto updater for OneLauncher
-  1.2 -- Add addon manager (plugins, themes, and abc files)
-  1.3 -- Implement extended lua plugin api (More keyboard action interupts, ect)
-  1.4 -- Add Lutris integration, full game install from OneLauncher, and stuff like dxvk support/auto setup in own prefixes
