#!/usr/bin/env python
# coding=utf-8
import PyLotROLauncher.Information
import sys
import os
import shutil
from distutils.core import setup
import py2exe

py2exeMode = False

for arg in sys.argv:
	if arg == 'py2exe':
		py2exeMode = True

if not py2exeMode:
	sys.argv = sys.argv + ['py2exe']

setup(name = "PyLotROLauncher",
	version = PyLotROLauncher.Information.Version,
	description = PyLotROLauncher.Information.Description,
	author = PyLotROLauncher.Information.Author,
	author_email = PyLotROLauncher.Information.Email,
	url = PyLotROLauncher.Information.WebSite,
	packages = ['PyLotROLauncher'],
	scripts = ["pylotro"],
	package_data = {'PyLotROLauncher' : ["*.png", "ui/*", "images/*"] },
	data_files = [('PyLotROLauncher/ui', ["PyLotROLauncher/ui/winMain.ui", "PyLotROLauncher/ui/winAbout.ui",
		"PyLotROLauncher/ui/winCheckConfig.ui", "PyLotROLauncher/ui/winLog.ui",
		"PyLotROLauncher/ui/winSelectAccount.ui", "PyLotROLauncher/ui/winSettings.ui"]),
		('PyLotROLauncher/images', ["PyLotROLauncher/images/LotROLinux.png", "PyLotROLauncher/images/LotROLinux.ico",
		"PyLotROLauncher/images/DDOLinux.png", "PyLotROLauncher/images/DDOLinux.ico"])],
	long_description = PyLotROLauncher.Information.LongDescription ,
	windows = [{"script": "pylotro", "icon_resources": [(0, "PyLotRO_Menu.ico")]}],
	options = {"py2exe": {"includes": ["sip"]}}
)

