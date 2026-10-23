import importlib.metadata

from packaging.version import Version

# Metadata has been manually entered to work with Nuitka.
# See https://github.com/Nuitka/Nuitka/issues/2965
# ruff: ignore[ERA001]
# metadata = importlib.metadata.metadata(__package__)
# __title__ = metadata["Name"]
# __version__ = metadata["Version"]
# version_parsed = Version(__version__)
# __description__ = metadata["Summary"]
# # Update checks only work with a repository hosted on GitHub.
# __project_url__ = next(
#     url.split(",")[1].strip()
#     for url in metadata.get_all("Project-URL", ())
#     if url.lower().startswith("repository")
# )
# __author__, __author_email__ = parseaddr(metadata["Author-email"])
__title__ = "OneLauncher"
__version__ = importlib.metadata.version(__package__)
version_parsed = Version(__version__)
__description__ = "The OneLauncher to rule them all"
# Update checks only work with a repository hosted on GitHub.
__project_url__ = "https://github.com/JuneStepp/OneLauncher"
__author__ = "June Stepp"
__author_email__ = "contact@junestepp.me"

__copyright__ = "(C) 2019-2026 June Stepp"
__copyright_history__ = (
    "Based on PyLotRO\n(C) 2009-2010 AJackson\n"
    "Based on LotROLinux\n(C) 2007-2008 AJackson\n"
    "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy"
)
