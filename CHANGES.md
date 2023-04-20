Lord of the Rings Online and Dungeons & Dragons Online
Launcher for Linux, Windows, and Mac OS X

(C) 2019-2021 June Stepp

# Changes

1.2.9

    Update game server certificates.

1.2.8

    Just a quick fix for the in-game store with the 64-bit client on Windows.

1.2.7

    This release has a couple important fixes. Currently, major refactoring is under way for OneLauncher 2.0. If you would be interested in helping translate OneLauncher to French, German, or Russian then please contact me at `contact@JuneStepp.me` or anywhere else such as the OneLauncher GitHub page.

       - Fixed getting legendary servers status
       - Downgraded SSL cipher level for game servers. Fixes connection for some Linux distros. Fix by @gtbX
       - Fixed no Keyring backend being chosen when program is compiled with Nuitka
       - Fixed window dragging on Wayland

1.2.6

    This release implements some important fixes for the addon manager and adds the --language launch argument.

        * Removed unused import
        * Re-enabled table headers that got automatically disabled in addon manager
        * Fixed addon manager UI breaking when OS text size is changed
        * Added launch argument to set the game client language. This was requested by @wduda for easier plugin testing

1.2.5

    This is a quick hotfix for the in-game store with the 64-bit client on Windows. The WINE version is also updated for Mac and Linux users.

        * Fixed in-game store issue on Windows builds with the 64-bit client
        * Updated WINE

1.2.4

    This release has some small improvements and important fixes. Most importantly the certificates needed for logging into LOTRO have been updated and a bug affecting the installation of some plugins has been fixed. Thanks to @mja00 and @gtbX for their code contributions to this update.

        * Support for the Win32 legacy client in the UI
        * Improved element spacing in the settings window
        * Updated WINE and DXVK
        * Added just in case check to stop plugin folder from being accidentally deleted
        * Minor code style fixes
        * Fixed installation of plugins with file names that include the plugin's root folder name
        * Updated to PySide6. This allows OneLauncher to run on LMDE
        * Setup Poetry for dependency management
        * Fixed buttons in addon manager that overlapped other elements
        * Simplified loading of news feeds
        * Updated the certificates for SSL connections



1.2.3

    This release has some small fixes and improvements. Most notably FSYNC support is added and the first language detected is used by default rather than English. This improves the user experience for those that don't have English installed with their client.

        * Updated WINE and DXVK
        * Fixed typo in change log
        * Improved handling of network errors
        * Refactored code with Sourcery.ai
        * Support for Proton (Has to be manually set up in WinePrefix.py)
        * Manually refactored InstallAddon function
        * Fixed logging in WinePrefix.py
        * FSYNC support
        * OneLauncher change logs display in Markdown format
        * Language defaults to first one detected rather than English
        * Fixed getting normalClientNode when it doesn't exist yet

1.2.2

    This release fixes language selection and allows specification of startup game with a launch argument. This can be used to make different shortcuts for quickly accessing OneLauncher with different games.

        * Fixed language selection
        * Startup game selection with `--game` launch argument
        * Advanced usage section in README.md

1.2.1

    This release fixes some important bugs and allows developers to request a Python script to be run on every game launch. **The user has to give permission for every add-on that does this since these scripts have the equivalent power of an executable file.**

        * Dynamic documents folder detection on Windows
        * Fixed .plugincompendium file finding on Windows
        * Switch to using game config values for game settings and log folders
        * Database is re-made if its structure doesn't match current generation code
        * Startup script support for add-ons
        * Invalid folder handling for plugins and music
        * A few smaller fixes and improvements

1.2

    The main feature of this release is the add-on manager, but a ton more was done. Thanks to everyone on the LOTRO discord server who helped out with testing. Especially the ever detail oriented ShoeMaker/Technical-13.

        *  Add-on manager
             Manage, update, and browse/download
                 *  plugins (with dependency checking)
                 *  themes (DDO support too!)
                 *  music (.abc files/collections of files)
        * Multiple accounts support
        * Fixed patching on Windows
        * Improved setup wizard
        * Better preview clients support
        * Switch to installer and cx-freeze for distribution
        * Many smaller improvements

1.1

    This is a big release that adds a lot of polish and usability to OneLauncher. With the built in prefix it is now possible to always run LOTRO and DDO in the best way possible without any knowledge of Wine. Even an install on a separate windows partition should work!

      *  Redone setup wizard
      *  Auto setup OneLauncher Wine prefix (In game stores should work)
            *  Built in dxvk support (Lets directx11 get used with lotro and ddo)
            *  Built in esync support
            *  Built in wine downloading (Separate wine should still be installed for dependencies)
      *  Option to securely remember account password
      *  Window dragging
      *  Redone language selection
      *  Many smaller improvements

1.0

    My first release with many updates for the modern day and design improvements. I'm having a lot of fun with this, so I hope you enjoy it too!
      * Redone ui
      * 64-bit client support
      * Update to PyQt5
      * New PyInstaller based building system to one executable
      * Rebrand to OneLauncher
      * Many smaller improvements

<hr>Below this is PyLotRO. Above is when it became OneLauncher<hr/>

0.2.6

    Updated certificate chain to new SSL certificates after recent update (22.0.1 or possibly 22) update
        by SSG broke authentication using the old certs.

0.2.5

    Added code to check for local game client override in TurbineLauncher.exe.config in game
        directory.  This is to handle workaround from SSG for game client crashes on
        Windows XP/Vista platforms that also affects Linux users running the game under
        wine.  For more information see link below.

        https://www.lotro.com/forums/showthread.php?654273-Windows-XP-and-Vista-Launcher-Issues-Solution

0.2.4

    News feed fixed - Apparently Turbine changed the content encoding of the news feed to
        gzip and retrieving the news feed was failing.  We now accept gzip content
        encoding for the news feed by default and check the Content-Encoding header and
        uncompress if content is gzip.
        Also some palette adjustments to the widgets (darker theme)

0.2.3

    Localization changes from hcjiv1 and Arek75. Turbine has removed the client local
        files for each language. Now each language has a separate subdirectory. If
        the client local file is not found then I (hcjiv1) pick languages based on those
        subdirectories.  Thanks to hcjiv1 and Arek75.  Version bump to 0.2.3

0.2.2

    Fixes for Update 15.1 changes to launcher.config argument template.  Turbine is now
        using crashserverurl and DefaultUploadThrottleMbps in the argument template.
        Version bump to 0.2.2.

0.2.1

    Fixes for launcher.config XML Changes and version bump to 0.2.1
        Fix for 20-Nov-2014 slight changes to WorldQueue.config by Turbine which
        broke pylotro.

0.2.0

    Fix newsfeed (again) after site revamp
        Fix XML parsing	that relied on consistent behaviour of undefined ordering
        Fix problems when path settings have trailing (back-)slashes.
        Support for Python 3.x, PyQt 4.6+ and OpenSSL 1.x
        Enable server authentication for better security (Python 3.2+ only currently)

0.1.15

    Fix problem getting newsfeed (might be temp glitch)
        Fix EN GB -> English problem

0.1.14

    Get proper CSS file for newsfeed
            New error [E14] if game account not linked to user account

0.1.13

    LotRO is now F2P, remove account check

0.1.12

    Display status code on E08 errors
            Save returned data from servers

0.1.11

    Now that DDO is free-to-play there is no longer a need to
            reject accounts flagged as inactive (DDO only)

0.1.10

    Switch to using pyinstaller rather than py2exe (can now build via wine)
            Configuration wizard now works on Windows version

0.1.9

    Make ConfigCheck work when in a CX/Wine bottle
            Fixed issue with incorrect font size on Windows version

0.1.8.2

    Fixed error in JoinWorldQueue, not recognising if join failed

0.1.8

    Fixed problem with windows icon not showing up on some set-ups
            Added a native version of the options window

0.1.7

    Fixed problem that was stopping Windows version use
            proper web browser widget
            Windows version now smaller in size (due to allowing py2exe to
            put all pyc files in zip file)
            Due to issues with child windows drawing under the parent
            window on some systems, add option under tools so that all
            child windows hide the parent and then redisplay the parent
            when finished
            Due to the windows version providing a standalone solution
            the generation of a Mac OS X app file has been withdrawn

0.1.6.2

    Fix winMain.ui to stop launcher failing on Hardy

0.1.6.1

    Use APPDATA rather than USERPROFILE when running under Windows

0.1.6

    Remove 4suite as dependency
            Added compatibility for working under Windows

0.1.5

    Fixed problem with launcher consuming high CPU when client running

0.1.4

    Log windows (Patch/Run Game) exit button renamed
            abort while running - display message when finished/aborted
            Finished MacOSX .app file functions
            DDO test server uses login queues [365538]
            Some versions of PyQt4 had problem with multi-line message
            in ui/winSelectAccount.ui [365541]

0.1.3

    Fixed error in AuthenticateUser
            Added make_app to setup.py to allow creation of
            MacOSX .app file
            Added configuration checker
            Convert code to be compatibile with Py3.0 as well as Py2.x

0.1.2

    Improved error trapping when servers are down
            Rename PyLotRO folder PyLotROLauncher so that
            people extracting on Windows didn't get errors

0.1.1

    Add uninstall option to setup.py
            Fixed SettingsWizard problem with returning path
            Fixed MainWindow thread not return data correctly

0.1.0

    Initial version of PyLotRO, direct port from LotROLinux

<hr>Below this is LotROLinux (C# Program).  Above is when it became PyLotRO (Python Program)<hr/>

0.9.8 

    Corrected problem with patching if in different
        WINEPREFIX

0.9.7 

    If no login queue URLs are returned skip
        the join world queue section of the LOTRO login

0.9.6 

    Fetch correct news stream based on language code

0.9.5 

    Fixed following bugs:
        User/Pass error being misreported
        Failing to run if bottle name contains spaces
        Not displaying error if patch function not found
        Mini-HTML not handling font tags

0.9.4 

    Fixed a bug where the patcher would abort if
        there was no bindat or temp folders

        Find correct path for CX using $CX_ROOT on Mac OSX

0.9.3 

    Removed complex patch window and recoded the
        simple patch window to be more responsive

        DDO falls back to dndlauncher.exe.config if
        TurbineLauncher.exe.config not found in the
        game directory

0.9.2 

    DDO seems to use TurbineLauncher.exe.config
        now instead of dndlauncher.exe.config

0.9.1 

    Implement queue system (LOTRO only)

        Remove old configuration import functions

        Alter configuration so that all settings
        are game dependant (like ULL)

        Make Crossover functionality more
        user friendly

        Removed GTKHtml Browser to help use on Macs

        Heavily improved Mac support

0.9  

    Added support for Crossover Games

0.8   

    Swapped to GPL v3.

0.7.7 

    When in DDO mode the settings window lets you specify
        the name for patchclient.dll

0.7.6 

    If multiple game accounts exist for the specified
        user account then display a window to allow user
        to choose which account to use

0.7.5 

    Added a simple status window version of the
        patch window as US version still causing problems.

0.7.4 

    Prevent launcher crashing if authentification
        server is down

        You can now have two versions of LOTRO and two of DDO
        (for anyone who has the test client or just needs
        more than one)

        Switched to using gmcs & 2.0 of the framework for
        better list and string handling.

0.7.3 

    Display warning if game directory
        not found and disable patch function

        Fixed problem with unicode characters
        causing authentication problems

        Various config files fetched from servers
        now saved with same names as CLI launcher

0.7.2 

    Exceptions raised during patching
        process should now be handled

        Added option to save wine output
        to file run.log in config directory

        Patching process should handle
        incorrect version of patchclient.dll
        and the log file being locked

        Added .desktop file & icon

0.7.1 

    Fixed problem with realm not being
        saved correctly in config file and
        a coredump problem with the gecko
        browser when switching games

0.7   

    Install the game using make install,
        no need to manually copy files also
        can be ran from anywhere so no need
        to change into the game directory

        Converted GUI from Stetic to Glade

0.6.1 

    Fixed problem with status windows
        not scrolling correctly

0.6   

    Patch option added under Options
        tab. At present the hi-res graphics
        files are not patched.

        before attempting net access

0.5.4 

    Added option to disable hi-res
        graphics

0.5.3 

    Fixed another authentication
        problem caused by having an
        active & inactive LOTRO subscription

0.5.2 

    Fixed another bug causing problems
        authenticating some accounts

0.5.1 

    Fixed bug with game authenticating
        wrong game if multiple game entries
        exist on auth server (ie one for LOTRO
        and one for DDO)

0.5   

    Launcher now detects if game folder
        contains Lord of the Rings Online
        or Dungeons & Dragons Online and
        reconfigures itself accordingly.

0.4   

    News fetched in separate thread
        to improve start up time.

        Languages now shown in non-code
        format.

0.3.2 

    Corrected configure instructions.

        Launcher now randomly chooses which
        login queue to use if there is more
        than one.

        Tidied code up a bit and recreated
        the files needed to build the executable.

0.3.1 

    Disabled support for gecko/firefox

0.3   

    Executable name changed to LotROLinux.run
        to avoid confusion with a .exe extension.

        Package is now a source ball to avoid
        library version compatability problems.

0.2   

    Account authentification should now work
        for non-EU users.

        Added support for gecko/firefox

<hr>Below this is CLI launcher for
LOTRO (Shell Script). Above is when it became LotROLinux (C# Program)<hr/>

v.1.2.1 2016-06-10	

    fixed link to urlencode.sh (.de -> .com)
			broken link pointed out by Charles Tersteeg

v1.2.0  2014-12-15	

    update to configuration and template generation, /AGAIN/
			contributor: blosco in the official LotRO forum

v1.1.1  2014-11-27	

    fixed bug in language for arg template, introduced by 1.1.0
			contributor: Etienne Carriere

v1.1.0  2014-11-25	

    update to configuration "parser" and game template generation
			 necessary to reflect changes to the game configuration files
			contributor: blosco (and others) in the official LotRO forum

v1.0.1  2014-04-09	

    added comment for forcing SSLv3
			minor cosmetic and typo fixes to the ChangeLog
			contributor: Nicolas Trecourt (SSLv3 symptom and workaround)

v1.0    2013-10-02	

    added patch progress helper
			also added updates to loading screens
			enabled re-use of existing login ticket (for up to 12 hours)
			other small changes and cleanups

v1.0rc2 2011-08-09	

    small update for global service (grep -F for server names)

v1.0rc1 2010-11-25	

    updates for F2P
			added queue looping
			minor cleanups
			contributor: steelsnake (queue loop)

v0.9.9d 2008-10-27	

    added check for disabled world login queue

v0.9.9c 2008-04-10	

    added choice for patching (default: start without patching)
			changed language check to now return the proper language
			 code so that the patching works properly now wrt.
			 the splash screen (ie: DE->de EN->en EN_GB->en_GB)
			added choice for subscription to use when more than one
			 <GameSubscription> sections exist in GLSAuthServer config
			contributors: ct_traveller and JediMastyre (multiple subscriptions)

v0.9.9b 2008-01-28	

    fixed an issue with the GLSDataCenter config file downloaded
			 from Turbine containing more than one <Datacenter> section

v0.9.9  2008-01-02	

    MAJOR breakthrough with the patching
			earlier attempts at linking against the dll functions stalled
			 due to missing function prototypes
			blatantly simple call using the rundll interface does the trick
			contributor: Robert Getter ("rundll32.exe PatchClient,Patch")

v0.9.7  2007-11-20	

    can now be called from elsewhere, will change to the game dir
			 (still needs to reside there, of course)

v0.9.6  2007-08-07	

    changed account id extraction to look for the correct game, too
			so that it works for subscribers of other turbine games (DDO)
			contributor: thealb

v0.9.5  2007-05-30	

    changed to SOAP for LoginAccount as well (same reason as 0.9.4)
			SOAP snippet taken from lotroeugls.com service description
			also switched off wine debugging msgs to increase performance
			contributor: kegie (suggested WINEDEBUG=fixme-all)

v0.9.4  2007-05-29	

    changed to SOAP for GetDatacenters due to non-EU LOTRO
			datacenter (US/AU/others) not accepting HTTP GET
			contributor: Fitzy_oz (SOAP request body)

v0.9.3  2007-05-27	

    fixed extractions for XML value="$VAL"
			contributor: ajackson (problem identified)

v0.9.2  2007-05-25	

    added check for installed languages and chooser
			contributor: Sinistral

v0.9.1  2007-05-24	

    "parsing" TurbineLauncher.exe.config

v0.9    2007-05-05	

    initial version
