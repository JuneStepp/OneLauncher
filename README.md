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
(c) 2019 Jeremy Stepp

Based on PyLotRO
(C) 2009 AJackson

Based on LotROLinux
(C) 2007-2008 AJackson

Based on CLI launcher for
LOTRO (C) 2007-2009 SNy

# Basic Use

 Simply download the appropriate executable for you operating system and double click it!

# Development Install

The following items are required
to run OneLauncher from source.

-   Python (3.2+)
-   qtpy (Can be installed with pip)
-   PyQt5 (Can be installed with pip)
-   qdarkstyle (Can be installed with pip)
-   pkg_resources (Comes with setuptools. You probably have it, but it can be installed with pip)

-   PyInstaller (Needed to build. Can be installed with pip.
    Currently [development version](https://github.com/pyinstaller/pyinstaller/archive/develop.zip) is needed)
-   pywin32 (Needed for Windows building. Can be installed with pip)

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
