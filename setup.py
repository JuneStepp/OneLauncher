#!/usr/bin/env python
# coding=utf-8
from distutils.core import setup
import PyLotROLauncher.Information
import sys
import os

installMode = False
uninstallMode = False
for arg in sys.argv:
	if arg == 'install':
		installMode = True
	elif arg == 'uninstall':
		uninstallMode = True

if uninstallMode:
	logfile = open("pylotro-install.log", "r")

	for filename in logfile.readlines():
		tempfile = filename.replace("\n", "") 
		print("removing " + tempfile)
		os.remove(tempfile)

	logfile.close()
	os.remove("pylotro-install.log")
else:
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
		package_data = {'PyLotROLauncher' : ["*.png", "ui/*", "images/*"] },
		data_files = [('share/pixmaps', ['PyLotRO_Menu.png']),
			('share/applications',['PyLotRO.desktop']),],
		long_description = PyLotROLauncher.Information.LongDescription 
	)

