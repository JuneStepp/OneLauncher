The OneLauncher is a custom launcher for The Lord of the Rings Online and Dungeons & Dragons Online
for Linux, Windows, and Mac OS X based on PyLotRO by AJackson. PyLotRO
was originally made to allow Linux and Mac players to enjoy LOTRO, but fell
out of relevance once it was no longer needed. This project aims to make a launcher
with new and interesting features that will always be available whether it's for private
servers after the games have shut down, if the main launcher stops working on Linux, or
if people see that it is The OneLauncher to Rule Them All and use it for that reason too.
It is actually mainly being developed as a fun learning experience for me and to show my
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

 Simply download the appropriate executable for you operating system and double click it!

# Development Install

The following items are required
to run OneLauncher from source.

-   Python (3.2+)
-   PyQt5 (Can be installed with pip)
-   PyQtWebEngine (Can be installed with pip)
-   qdarkstyle (Can be isntalled with pip)

-   pythoninstaller (Needed to build. Can be installed with pip.
    Currently [development version](https://github.com/pyinstaller/pyinstaller/archive/develop.zip) is needed

recommended optional package:
pkg_resources

# To run

`./RunOneLauncher`

Or.

`python3 RunOneLauncher`

# To build

`python3 build.py`

The project can only be built for the os that the build script is run on,
so it has to be built on every target os individually. The building output
for Linux can only be run on systems as up to date or more as the system it
is built on, so an old os may want to be built on. The binary for Linux is
also not cross architecture compatible.

A settings wizard exists that can attempt to
find relevant installations of LotRO or DDO.
For CrossOver and CrossOver Games it searches
in the default bottle location. For Wine it
looks for wine folders in your home directory
(folders starting with a full stop with a
directory called drive_c under that). For all
options it tries to find the game in the
"Program Files" directory (or directories off
that). If your game is installed elsewhere then
you will need to manually configure the game.

The wizard will default hi-res graphics to
enabled if it finds the file associated with
that (client_highres.dat) in the game folder.
Note the DLL used for patching is set to
patchclient.dll, for DDO you will need to enter
the options window and manually change it if
you wish to patch the game (see below).

To switch between the launcher using it's
settings for Lord of the Rings Online and
Dungeons & Dragons Online select the Switch
option under the Options menu.

To patch the game files with official patches
released by StandingStoneGames select the
Patch from the Options menu and follow the
instructions.

You can change your settings via the
Settings -> Options menu.

All options are game dependant (ie can be set
differently for LOTRO and DDO).

If save these settings is ticked then your
account name, language and realm selection
are saved when you successfully login.

NB: Your password is not saved for security
reasons.
