Lord of the Rings Online and Dungeons & Dragons Online
Launcher for Linux, Windows, and Mac OS X

(C) 2019-2020-2020 Jeremy Stepp

# Changes

1.2 (Unreleased)

        *  Addon manager
             Manage, update, and browse/download
                 *  plugins (with dependency checking)
                 *  themes (DDO support too!)
                 *  music (.abc files/collections off files)
        * Self updater
        * Multiple accounts support
        * Custom directory selection in setup wizard
        * Many more smaller improvements

1.1

    This is a big release that adds a lot of polish and usability to OneLauncher. With the built in prefix it is now possible to always run LOTRO and DDO in the best way possible without any knowledge of Wine. Even an install on a separate windows partition should work!

      *  Redone setup wizard
      *  Auto setup OneLauncher Wine prefix (In game stores should work)
            *  Built in dxvk support (Lets directx11 get used with lotro and ddo)
            *  Built in esync support
            *  Built in wine downloading (Seperate wine should still be installed for dependencies)
      *  Option to securely remember account password
      *  Window dragging
      *  Redone language selection
      *  Many more smaller improvements

1.0

    My first release with many updates for the modern day and design improvements. I'm having a lot of fun with this, so I hope you enjoy it too!
      * Redone ui
      * 64-bit client support
      * Update to PyQt5
      * New pyinstaller based building system to one executable
      * Rebrand to OneLauncher
      * Many more smaller improvements

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
