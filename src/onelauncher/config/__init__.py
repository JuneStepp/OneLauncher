from platformdirs import PlatformDirs

from .. import __title__

platform_dirs = PlatformDirs(__title__.lower(), False)
