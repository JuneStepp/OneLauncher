import importlib_metadata

package_metadata = importlib_metadata.metadata(__package__)
__title__ = package_metadata["Name"]
__version__ = package_metadata["Version"]
__description__ = package_metadata["Summary"]
# Update checks only work with a repository hosted on GitHub.
__project_url__ = package_metadata.get("Home-page")
__author__ = package_metadata.get("Author")
__author_email__ = package_metadata.get("Author-email")
__license__ = package_metadata.get("License")
__copyright__ = "(C) 2019-2024 June Stepp"
__copyright_history__ = (
    "Based on PyLotRO\n(C) 2009-2010 AJackson\n"
    "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy\n"
    "Based on CLI launcher for LOTRO\n(C) 2007-2010 SNy"
)
