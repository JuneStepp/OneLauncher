from platformdirs import PlatformDirs

from ..__about__ import __title__

platform_dirs = PlatformDirs(__title__.lower(), False)
