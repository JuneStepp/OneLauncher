#!/usr/bin/env python
# coding=utf-8
import PyLotROLauncher.Information
import sys
import os
import shutil
from distutils.core import setup

installMode = False
uninstallMode = False
makeAppMode = False

for arg in sys.argv:
	if arg == 'install':
		installMode = True
	elif arg == 'uninstall':
		uninstallMode = True
	elif arg == 'make_app':
		makeAppMode = True

if makeAppMode:		# User wishes to make a Mac OS X app file
	if os.path.exists(os.path.join("dist", "PyLotRO.app")):
		shutil.rmtree(os.path.join("dist", "PyLotRO.app"))

	print("Creating app file structure...")
	os.makedirs(os.path.join("dist", "PyLotRO.app", "Contents", "MacOS"))
	os.makedirs(os.path.join("dist", "PyLotRO.app", "Contents", "Resources"))

	print("Copying PyLotRO to app file structure...")
	shutil.copytree("PyLotROLauncher", os.path.join("dist", "PyLotRO.app", "Contents", "Resources", "PyLotROLauncher"))
	shutil.copy(os.path.join("MacOSX", "PyLotRO"), os.path.join("dist", "PyLotRO.app", "Contents", "MacOS", "PyLotRO"))
	shutil.copy(os.path.join("MacOSX", "PyLotRO.icns"), os.path.join("dist", "PyLotRO.app", "Contents",
		"Resources", "PyLotRO.icns"))
	shutil.copy(os.path.join("MacOSX", "Info.plist"), os.path.join("dist", "PyLotRO.app", "Contents", "Info.plist"))
	shutil.copy("pylotro", os.path.join("dist", "PyLotRO.app", "Contents", "Resources", "pylotro"))
	print("App file created")
elif uninstallMode:
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
	# If called with install capture the installation to to pylotro-install.log
	if installMode:
		sys.argv = sys.argv + ['--record', 'pylotro-install.log']

	setup(name = "PyLotROLauncher",
		version = PyLotROLauncher.Information.Version,
		description = PyLotROLauncher.Information.Description,
		author = PyLotROLauncher.Information.Author,
		author_email = PyLotROLauncher.Information.Email,
		url = PyLotROLauncher.Information.WebSite,
		packages = ['PyLotROLauncher'],
		scripts = ["pylotro"],
		data_files = [('share/pixmaps', ['PyLotRO_Menu.png']),
			('share/applications',['PyLotRO.desktop']),],
		package_data = {'PyLotROLauncher' : ["*.png", "ui/*", "images/*"] },
		long_description = PyLotROLauncher.Information.LongDescription 
	)

