import importlib.metadata

from packaging.version import Version

# Metadata has been temporily manually entered to work with Nuitka.
# See https://github.com/Nuitka/Nuitka/issues/2965

# metadata = importlib.metadata.metadata(__package__)   # noqa: ERA001
__title__ = "OneLauncher"
__version__ = importlib.metadata.version(__package__)
__description__ = "The OneLauncher to rule them all"
__project_url__ = "https://github.com/JuneStepp/OneLauncher"
__author__ = "June Stepp"
__author_email__ = "contact@junestepp.me"
__license__ = "GPL-3.0-or-later"
# __title__ = metadata["Name"]  # noqa: ERA001
# __version__ = metadata["Version"]  # noqa: ERA001
version_parsed = Version(__version__)
# __description__ = metadata["Summary"]  # noqa: ERA001
# # Update checks only work with a repository hosted on GitHub.
# __project_url__ = metadata.get("Home-page")  # noqa: ERA001
# __author__ = metadata.get("Author")  # noqa: ERA001
# __author_email__ = metadata.get("Author-email")  # noqa: ERA001
# __license__ = metadata.get("License")  # noqa: ERA001
__copyright__ = "(C) 2019-2024 June Stepp"
__copyright_history__ = (
    "Based on PyLotRO\n(C) 2009-2010 AJackson\n"
    "Based on LotROLinux\n(C) 2007-2008 AJackson\n"
    "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy"
)
