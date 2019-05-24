#!/usr/bin/env python3
# coding=utf-8
import PyLotROLauncher.Information
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
    logfile = open("pylotro-install.log", "r")
    maindir = ""

    # read through the install log deleting every file installed
    for filename in logfile.readlines():
        tempfile = filename.replace("\n", "")
        print(("removing %s" % (tempfile)))
        os.remove(tempfile)

        # If the directory name ends with PyLotROLauncher then this is the base directory for the installation
        if os.path.dirname(tempfile).endswith("PyLotROLauncher"):
            maindir = os.path.dirname(tempfile)

    logfile.close()

    # Remove the base installation directory
    print(("removing %s" % (maindir)))
    shutil.rmtree(maindir)
    os.remove("pylotro-install.log")
else:
    opts = {}
    # If called with install capture the installation to to pylotro-install.log
    if installMode:
        opts["install"] = {"record": "pylotro-install.log"}

    setup(name="PyLotROLauncher",
          version=PyLotROLauncher.Information.Version,
          description=PyLotROLauncher.Information.Description,
          author=PyLotROLauncher.Information.Author,
          author_email=PyLotROLauncher.Information.Email,
          url=PyLotROLauncher.Information.WebSite,
          packages=['PyLotROLauncher'],
          scripts=["pylotro"],
          data_files=[('share/pixmaps', ['PyLotRO_Menu.png']),
                      ('share/applications', ['PyLotRO.desktop']), ],
          package_data={'PyLotROLauncher': [
              "*.png", "ui/*", "images/*", "certificates/*.pem"]},
          long_description=PyLotROLauncher.Information.LongDescription,
          options=opts
          )
