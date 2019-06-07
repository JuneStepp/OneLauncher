#!/usr/bin/env python3
# coding=utf-8
import OneLauncher.Information
import sys
import os
import shutil
from distutils.core import setup

installMode = False
uninstallMode = False

for arg in sys.argv:
    if arg == 'install':
        installMode = True
    elif arg == 'uninstall':
        uninstallMode = True

if uninstallMode:
    logfile = open("OneLauncher-install.log", "r")
    maindir = ""

    # read through the install log deleting every file installed
    for filename in logfile.readlines():
        tempfile = filename.replace("\n", "")
        print(("removing %s" % (tempfile)))
        os.remove(tempfile)

        # If the directory name ends with OneLauncher then this is the base directory for the installation
        if os.path.dirname(tempfile).endswith("OneLauncher"):
            maindir = os.path.dirname(tempfile)

    logfile.close()

    # Remove the base installation directory
    print(("removing %s" % (maindir)))
    shutil.rmtree(maindir)
    os.remove("OneLauncher-install.log")
else:
    opts = {}
    # If called with install capture the installation to to OneLauncher-install.log
    if installMode:
        opts["install"] = {"record": "OneLauncher-install.log"}

    setup(name="OneLauncher",
          version=OneLauncher.Information.Version,
          description=OneLauncher.Information.Description,
          author=OneLauncher.Information.Author,
          author_email=OneLauncher.Information.Email,
          url=OneLauncher.Information.WebSite,
          packages=['OneLauncher'],
          scripts=["RunOneLauncher"],
          data_files=[('share/pixmaps', ['OneLauncher_Menu.png']),
                      ('share/applications', ['OneLauncher.desktop']), ],
          package_data={'OneLauncher': [
              "*.png", "ui/*", "images/*", "certificates/*.pem"]},
          long_description=OneLauncher.Information.LongDescription,
          options=opts
          )
