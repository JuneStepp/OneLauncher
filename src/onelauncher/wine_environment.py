###########################################################################
# Code for managing WINE. This code should not be called on Windows, as
# WINE is neither supported or needed there.
#
# Based on PyLotRO
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# Based on LotROLinux
# (C) 2007-2008 AJackson <ajackson@bcs.org.uk>
#
#
# (C) 2019-2026 June Stepp <contact@JuneStepp.me>
#
# This file is part of OneLauncher
#
# OneLauncher is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# OneLauncher is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OneLauncher.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################
import logging
import lzma
import os
import ssl
import sys
import tarfile
from functools import partial
from pathlib import Path
from shutil import move, rmtree
from tempfile import TemporaryDirectory
from types import MappingProxyType
from typing import Final
from urllib import request
from urllib.error import HTTPError, URLError

import attrs
import certifi
from PySide6 import QtCore, QtWidgets

from .config import platform_dirs
from .ui.qtapp import get_qapp
from .ui.utilities import show_warning_message
from .wine.config import WineConfigSection

logger = logging.getLogger(__name__)


if sys.platform == "darwin":
    WINE_VERSION = "WS12WineSikarugir10.0_2"
    WINE_URL = "https://github.com/Sikarugir-App/Engines/releases/download/v1.0/WS12WineSikarugir10.0_2.tar.xz"

else:
    # To use Proton, replace link with Proton build and uncomment
    # `self.proton_documents_symlinker()` in wine_setup in wine_management
    WINE_VERSION = "10.20-staging-tkg-amd64-wow64"
    WINE_URL = "https://github.com/Kron4ek/Wine-Builds/releases/download/10.20/wine-10.20-staging-tkg-amd64-wow64.tar.xz"

DXVK_VERSION = "2.7.1"
DXVK_URL = (
    "https://github.com/doitsujin/dxvk/releases/download/v2.7.1/dxvk-2.7.1.tar.gz"
)

# macOS only. Includes DXVK.
SIKARUGIR_FRAMEWORKS_VERSION = "Template-1.0.5"
SIKARUGIR_FRAMEWORKS_URL = "https://github.com/Sikarugir-App/Wrapper/releases/download/v1.0/Template-1.0.5.tar.xz"


@attrs.define
class WineEnvironment:
    builtin_prefix_enabled: bool = True
    user_wine_executable_path: Path | None = None
    user_prefix_path: Path | None = None
    debug_level: str | None = None


class WineManagement:
    def __init__(self) -> None:
        self.is_setup = False

        self.prefix_path: Final[Path] = platform_dirs.user_cache_path / "wine/prefix"
        self.prefix_system32: Final[Path] = (
            self.prefix_path / "drive_c/windows/system32"
        )
        self.prefix_syswow64: Final[Path] = (
            self.prefix_path / "drive_c/windows/syswow64"
        )

        self.downloads_path: Final[Path] = platform_dirs.user_data_path / "wine"
        self.latest_wine_path: Final[Path] = (
            self.downloads_path / f"wine-{WINE_VERSION}"
        )
        self.wine_binary_path: Final[Path] = self.latest_wine_path / "bin" / "wine"

        self.latest_dxvk_path: Final[Path] = (
            self.downloads_path / f"dxvk-{DXVK_VERSION}"
        )
        self.latest_sikarugir_frameworks_path: Final[Path] = (
            self.downloads_path / f"frameworks-{SIKARUGIR_FRAMEWORKS_VERSION}"
        )

        self._dlgDownloader: QtWidgets.QProgressDialog | None = None

    @property
    def dlgDownloader(self) -> QtWidgets.QProgressDialog:
        if self._dlgDownloader is None:
            self._dlgDownloader = self.create_progress_dialog()
        return self._dlgDownloader

    @dlgDownloader.setter
    def dlgDownloader(self, new_value: QtWidgets.QProgressDialog) -> None:
        self._dlgDownloader = new_value

    def create_progress_dialog(self) -> QtWidgets.QProgressDialog:
        dialog = QtWidgets.QProgressDialog(
            "Checking for updates...",
            "",
            0,
            100,
            get_qapp().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint,
        )
        dialog.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        dialog.setAutoClose(False)
        dialog.setCancelButton(None)
        return dialog

    def _downloader(self, url: str, path: Path) -> bool:
        """Downloads file from url to path and shows progress with self.handle_download_progress"""
        try:
            ssl._create_default_https_context = partial(
                ssl.create_default_context, cafile=certifi.where()
            )
            request.urlretrieve(  # noqa: S310
                url, str(path), self._handle_download_progress
            )
            return True
        except (URLError, HTTPError):
            logger.exception("")
            show_warning_message(
                f"There was an error downloading '{url}'. "
                "You may want to check your network connection.",
                get_qapp().activeWindow(),
            )
            return False

    def _handle_download_progress(self, index: int, frame: int, size: int) -> None:
        """Updates progress bar with download progress"""
        percent = 100 * index * frame // size
        self.dlgDownloader.setValue(percent)

    def wine_setup(self) -> None:
        """Sets wine program and downloads wine if it is not there or a new version is needed"""

        # Uncomment line below when using Proton
        # self.proton_documents_symlinker()  # noqa: ERA001

        if self.wine_binary_path.exists():
            return

        self.dlgDownloader.setLabelText("Downloading WINE...")

        with TemporaryDirectory() as temp_dir_name:
            download_path = Path(temp_dir_name) / "wine.tar.xz"

            if not self._downloader(WINE_URL, download_path):
                return

            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting WINE...")
            self.dlgDownloader.setValue(99)
            self._wine_extractor(download_path)
            self.dlgDownloader.setValue(100)

    def proton_documents_symlinker(self) -> None:
        """
        Symlinks prefix documents folder to system documents folder.path
        This is needed for Proton.
        """
        prefix_documents_folder = (
            self.prefix_path / "drive_c/users/steamuser/My Documents"
        )

        # Will assume that the user has set something else up for now if the
        # folder already exists
        if prefix_documents_folder.exists():
            return

        # Make sure system documents folder and prefix documents root folder
        # exists
        platform_dirs.user_documents_path.mkdir(exist_ok=True)
        prefix_documents_folder.parent.mkdir(exist_ok=True, parents=True)

        # Make symlink to system documents folder
        platform_dirs.user_documents_path.symlink_to(
            prefix_documents_folder, target_is_directory=True
        )

    def _wine_extractor(self, archive_path: Path) -> None:
        with TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)

            # Extract tar.xz archive.
            with lzma.open(archive_path) as file, tarfile.open(fileobj=file) as tar:
                tar.extractall(temp_dir, filter="data")

            source_dir = next(temp_dir.glob("*/"))
            # Using `shutil.move` instead of `Path.rename`, so that it works across
            # filesystems.
            move(source_dir, self.latest_wine_path)

        # Remove old WINE versions.
        for folder in self.downloads_path.glob("*/"):
            if folder.name.startswith("wine") and folder != self.latest_wine_path:
                rmtree(folder)

    def dxvk_setup(self) -> None:
        if self.latest_dxvk_path.exists():
            if not (
                self.prefix_path / "drive_c/windows/system32/d3d11.dll"
            ).is_symlink():
                self._dxvk_injector()
            return

        self.dlgDownloader.setLabelText("Downloading DXVK...")
        with TemporaryDirectory() as temp_dir_name:
            download_path = Path(temp_dir_name) / "dxvk.tar.gz"

            if self._downloader(DXVK_URL, download_path):
                self.dlgDownloader.reset()
                self.dlgDownloader.setLabelText("Extracting DXVK...")
                self.dlgDownloader.setValue(99)
                self._dxvk_extractor(download_path)
                self.dlgDownloader.setValue(100)

        self._dxvk_injector()

    def _dxvk_extractor(self, archive_path: Path) -> None:
        with TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)

            # Extract the tar.gz archive.
            with tarfile.open(archive_path, "r:gz") as file:
                file.extractall(temp_dir, filter="data")

            source_dir = next(temp_dir.glob("*/"))
            # Using `shutil.move` instead of `Path.rename`, so that it works across
            # filesystems.
            move(source_dir, self.latest_dxvk_path)

        # Remove old DXVK versions.
        for folder in self.downloads_path.glob("*/"):
            if folder.name.startswith("dxvk") and folder != self.latest_dxvk_path:
                rmtree(folder)

    def _dxvk_injector(self) -> None:
        """Add DXVK to the WINE prefix"""
        dlls = (
            ("d3d10core.dll", "d3d11.dll")
            if sys.platform == "darwin"
            else ("dxgi.dll", "d3d10core.dll", "d3d11.dll", "d3d9.dll")
        )
        for dll in dlls:
            # Remove existing DLLs.
            (self.prefix_system32 / dll).unlink(missing_ok=True)
            (self.prefix_syswow64 / dll).unlink(missing_ok=True)

            # Symlink DXVK DLLs into the WINE prefix.
            (self.prefix_system32 / dll).symlink_to(self.latest_dxvk_path / "x64" / dll)
            (self.prefix_syswow64 / dll).symlink_to(self.latest_dxvk_path / "x32" / dll)

    def sikarugir_frameworks_setup(self) -> None:
        if self.latest_sikarugir_frameworks_path.exists():
            return

        self.dlgDownloader.setLabelText("Downloading WINE dependencies...")

        with TemporaryDirectory() as temp_dir_name:
            download_path = Path(temp_dir_name) / "sikarugir_frameworks.tar.xz"

            if not self._downloader(SIKARUGIR_FRAMEWORKS_URL, download_path):
                return

            self.dlgDownloader.reset()
            self.dlgDownloader.setLabelText("Extracting WINE dependencies...")
            self.dlgDownloader.setValue(99)
            self._sikarugir_frameworks_extractor(download_path)
            self.dlgDownloader.setValue(100)

    def _sikarugir_frameworks_extractor(self, archive_path: Path) -> None:
        with TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)

            # Extract the tar.xz archive.
            with lzma.open(archive_path) as file, tarfile.open(fileobj=file) as tar:
                tar.extractall(temp_dir, filter="data")

            source_dir = next(temp_dir.glob("*/")) / "Contents" / "Frameworks"
            # Using `shutil.move` instead of `Path.rename`, so that it works across
            # filesystems.
            move(source_dir, self.latest_sikarugir_frameworks_path)

        # Remove old versions.
        for folder in self.downloads_path.glob("*/"):
            if (
                folder.name.startswith("frameworks")
                and folder != self.latest_sikarugir_frameworks_path
            ):
                rmtree(folder)

    def setup_files(self) -> None:
        self.downloads_path.mkdir(parents=True, exist_ok=True)
        self.prefix_system32.mkdir(parents=True, exist_ok=True)
        self.prefix_syswow64.mkdir(parents=True, exist_ok=True)

        self.wine_setup()
        self.dlgDownloader.reset()
        if sys.platform == "darwin":
            self.sikarugir_frameworks_setup()
        else:
            self.dxvk_setup()
        self.dlgDownloader.close()
        self.is_setup = True


wine_management = WineManagement()


ESYNC_MINIMUM_OPEN_FILE_LIMIT = 524288


def get_wine_process_args(
    command: tuple[str | Path, ...],
    environment: MappingProxyType[str, str],
    wine_config: WineConfigSection,
) -> tuple[tuple[str | Path, ...], MappingProxyType[str, str]]:
    """Configure `run_process` arguments to use WINE."""
    if os.name == "nt":
        logger.warning("Attempt to use WINE on Windows. No changes were made.")
        return command, environment

    edited_environment = environment.copy()

    prefix_path: Path | None
    wine_path: Path | None
    if wine_config.builtin_prefix_enabled:
        if not wine_management.is_setup:
            wine_management.setup_files()

        prefix_path = wine_management.prefix_path
        wine_path = wine_management.wine_binary_path

        # Disable mscoree and mshtml to avoid downloading wine mono and gecko.
        wine_dll_overrides: list[str] = ["mscoree=d", "mshtml=d"]
        # Add dll overrides for DirectX, so DXVK is used instead of wine3d.
        if sys.platform != "darwin":
            wine_dll_overrides.extend(("d3d11=n", "dxgi=n", "d3d10core=n", "d3d9=n"))
        edited_environment["WINEDLLOVERRIDES"] = ";".join(wine_dll_overrides)

        if sys.platform != "darwin":
            # Enable ESYNC if open file limit is high enough.
            if (path := Path("/proc/sys/fs/file-max")).exists() and int(
                path.read_text()
            ) >= ESYNC_MINIMUM_OPEN_FILE_LIMIT:
                edited_environment["WINEESYNC"] = "1"

            # Enable FSYNC. It overrides ESYNC and will only be used if
            # the required kernel patches are installed.
            edited_environment["WINEFSYNC"] = "1"

        if sys.platform == "darwin":
            edited_environment["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(
                str(path)
                for path in (
                    (wine_management.latest_sikarugir_frameworks_path / "moltenvkcx"),
                    (wine_management.latest_wine_path / "lib"),
                    (wine_management.latest_wine_path / "lib64"),
                    wine_management.latest_sikarugir_frameworks_path,
                    Path("/opt/wine/lib"),
                    Path("/usr/lib"),
                    Path("/usr/libexec"),
                    Path("/usr/lib/system"),
                )
            )
            edited_environment["WINEDLLPATH_PREPEND"] = str(
                wine_management.latest_sikarugir_frameworks_path
                / "renderer"
                / "dxvk"
                / "wine"
            )

            # "wine doesn't handle VK_ERROR_DEVICE_LOST correctly"
            #     -- <https://github.com/Gcenx/macOS_Wine_builds/releases/tag/10.18>
            edited_environment["MVK_CONFIG_RESUME_LOST_DEVICE"] = "1"
    else:
        prefix_path = wine_config.user_prefix_path
        wine_path = wine_config.user_wine_executable_path

    if prefix_path:
        edited_environment["WINEPREFIX"] = str(prefix_path)

    edited_environment["WINEDEBUG"] = wine_config.debug_level or "-all"
    if "DXVK_LOG_LEVEL" not in edited_environment:
        edited_environment["DXVK_LOG_LEVEL"] = "error"

    return (wine_path if wine_path else "", *command), MappingProxyType(
        edited_environment
    )
