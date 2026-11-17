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
import errno
import hashlib
import logging
import os
import platform
import subprocess
import sys
from abc import ABC, abstractmethod
from functools import cached_property, partial
from pathlib import Path
from shutil import move, rmtree, unpack_archive
from tempfile import NamedTemporaryFile, TemporaryDirectory
from textwrap import dedent
from types import MappingProxyType
from typing import Final, Literal, assert_never, override

import attrs
import retryhttp
import trio
from httpx2 import HTTPError
from PySide6 import QtCore, QtWidgets
from retryhttp import (
    retry_if_network_error,
    retry_if_rate_limited,
    retry_if_server_error,
    retry_if_timeout,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_any,
    retry_if_exception_type,
    stop_after_attempt,
)

from onelauncher.network.httpx_client import get_httpx_client
from onelauncher.utilities import Progress, ProgressItem

from .config import platform_dirs
from .ui.qtapp import get_qapp
from .ui.utilities import show_warning_message
from .wine.config import WineConfigSection, WineMethod

logger = logging.getLogger(__name__)

ESYNC_MINIMUM_OPEN_FILE_LIMIT = 524288

KOSMICKRISP_MINIMUM_MACOS_VERSION = 26  # Tahoe


@attrs.define
class WineEnvironment:
    prefix_path: Final[Path] = platform_dirs.user_cache_path / "wine/prefix"
    downloads_path: Final[Path] = platform_dirs.user_data_path / "wine"
    env_vars: dict[str, str] = attrs.field(factory=dict)
    dll_overrides: list[str] = attrs.field(factory=list)

    @property
    def system32_path(self) -> Path:
        return self.prefix_path / "drive_c/windows/system32"

    @property
    def syswow64_path(self) -> Path:
        return self.prefix_path / "drive_c/windows/syswow64"

    def create_prefix(self) -> None:
        self.system32_path.mkdir(parents=True, exist_ok=True)
        self.syswow64_path.mkdir(parents=True, exist_ok=True)


@attrs.frozen(kw_only=True)
class HashMismatchError(ValueError):
    msg: str = "Hash mismatch error"
    url: str
    hash: str
    expected_hash: str


@attrs.frozen(kw_only=True)
class WineComponentDownloadError(Exception):
    msg: str = "Error downloading WINE component"


@attrs.frozen
class Component(ABC):
    wine_environment: WineEnvironment
    version: str
    url: str
    sha256_hash: str
    compression_format: str
    """See `shutil.get_unpack_formats()`"""

    @property
    def path(self) -> Path:
        return (
            self.wine_environment.downloads_path / f"{self.version}-{self.sha256_hash}"
        )

    @property
    def is_downloaded(self) -> bool:
        return self.path.exists()

    @retry(
        retry=retry_any(
            retry_if_server_error(),
            retry_if_network_error(),
            retry_if_timeout(),
            retry_if_rate_limited(),
            retry_if_exception_type(HashMismatchError),
        ),
        wait=retryhttp.wait_context_aware(),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.DEBUG),
        reraise=True,
    )
    async def download(
        self,
        progress: Progress,
    ) -> None:
        """
        Raises:
            HTTPError
            HashMismatchError
        """
        logger.debug("Downloading %s", self.url)

        progress_item = ProgressItem()
        progress.progress_items.append(progress_item)
        try:
            async with (
                get_httpx_client(self.url).stream(
                    "GET", self.url, follow_redirects=True
                ) as response,
                trio.wrap_file(NamedTemporaryFile()) as temp_download_file,
            ):
                response.raise_for_status()

                bytes_currently_downloaded = response.num_bytes_downloaded
                progress_item.total = int(
                    response.headers.get("Content-Length", 50000000)  # 50MB fallback.
                )
                download_hash = hashlib.new("sha256")
                async for chunk in response.aiter_bytes():
                    progress_item.completed += (
                        response.num_bytes_downloaded - bytes_currently_downloaded
                    )
                    bytes_currently_downloaded = response.num_bytes_downloaded
                    download_hash.update(chunk)
                    await temp_download_file.write(chunk)

                if download_hash.hexdigest() != self.sha256_hash:
                    raise HashMismatchError(
                        url=self.url,
                        hash=download_hash.hexdigest(),
                        expected_hash=self.sha256_hash,
                    )

                await temp_download_file.flush()
                with TemporaryDirectory() as temp_dir_str:
                    temp_dir = Path(temp_dir_str)
                    extracted = await trio.to_thread.run_sync(
                        self._extract, Path(temp_download_file.name), temp_dir
                    )
                    # Using `shutil.move` instead of `Path.rename`, so that it works across
                    # filesystems.
                    await trio.to_thread.run_sync(move, extracted, self.path)
        except Exception as e:
            progress.progress_items.remove(progress_item)
            raise e

    def _extract(self, archive_path: Path, extract_dir: Path) -> Path:
        unpack_archive(
            archive_path, extract_dir, format=self.compression_format, filter="data"
        )
        return next(extract_dir.glob("*/"))

    @abstractmethod
    def inject(self) -> None: ...


@attrs.frozen
class WineComponent(Component):
    wine_type: Literal["winehq", "sikarugir"]

    @override
    @property
    def path(self) -> Path:
        return super().path.parent / f"wine-{super().path.name}"

    @property
    def binary_path(self) -> Path:
        return self.path / "bin/wine"

    @override
    def _extract(self, archive_path: Path, extract_dir: Path) -> Path:
        source_dir = super()._extract(archive_path, extract_dir)

        if self.wine_type == "winehq" and sys.platform == "darwin":
            source_dir = source_dir / "Contents/Resources/wine"
            # Remove shipped dylibs, so Sikarugir ones are used.
            for dylib in source_dir.glob("lib/*.dylib"):
                dylib.unlink()

        return source_dir

    @override
    def inject(self) -> None:
        # Disable mscoree and mshtml to avoid downloading wine mono and gecko.
        self.wine_environment.dll_overrides.extend(("mscoree=d", "mshtml=d"))

        self.wine_environment.env_vars["WINEPREFIX"] = str(
            self.wine_environment.prefix_path
        )

        if sys.platform != "darwin":
            # Enable ESYNC if open file limit is high enough.
            if (path := Path("/proc/sys/fs/file-max")).exists() and int(
                path.read_text()
            ) >= ESYNC_MINIMUM_OPEN_FILE_LIMIT:
                self.wine_environment.env_vars["WINEESYNC"] = "1"

            # Enable FSYNC. It overrides ESYNC and will only be used if
            # the required kernel patches are installed.
            self.wine_environment.env_vars["WINEFSYNC"] = "1"

        if self.wine_type == "sikarugir":
            # Sikarugir 11 WINE will instantly exit without this.
            self.wine_environment.env_vars["SikarugirAppWine11"] = "1"


@attrs.frozen
class DxvkComponent(Component):
    @override
    @property
    def path(self) -> Path:
        return super().path.parent / f"dxvk-{super().path.name}"

    @override
    def inject(self) -> None:
        dlls = (
            ("d3d10core.dll", "d3d11.dll")
            if sys.platform == "darwin"
            else ("dxgi.dll", "d3d10core.dll", "d3d11.dll", "d3d9.dll")
        )
        for dll in dlls:
            # Remove existing DLLs.
            (self.wine_environment.system32_path / dll).unlink(missing_ok=True)
            (self.wine_environment.syswow64_path / dll).unlink(missing_ok=True)

            # Symlink DXVK DLLs into the WINE prefix.
            (self.wine_environment.system32_path / dll).symlink_to(
                self.path / "x64" / dll
            )
            (self.wine_environment.syswow64_path / dll).symlink_to(
                self.path / "x32" / dll
            )

        # Add dll overrides for DirectX, so DXVK is used instead of wine3d.
        if sys.platform == "darwin":
            self.wine_environment.dll_overrides.extend(("d3d11=n", "d3d10core=n"))
        else:
            self.wine_environment.dll_overrides.extend(
                ("d3d11=n", "dxgi=n", "d3d10core=n", "d3d9=n")
            )


@attrs.frozen
class D3dExtrasComponent(Component):
    @override
    @property
    def path(self) -> Path:
        return super().path.parent / f"d3d-extras-{super().path.name}"

    @override
    def inject(self) -> None:
        # Add native `d3dx11_42.dll` to the WINE prefix.
        # Native DLL needs to be used to fix frills memory leak potentially from
        # `D3DX11LoadTextureFromTexture` use which is a stub in WINE.
        dll = "d3dx11_42.dll"

        # Remove existing DLLs.
        (self.wine_environment.system32_path / dll).unlink(missing_ok=True)
        (self.wine_environment.syswow64_path / dll).unlink(missing_ok=True)

        # Symlink DXVK DLLs into the WINE prefix.
        (self.wine_environment.system32_path / dll).symlink_to(self.path / "x64" / dll)
        (self.wine_environment.syswow64_path / dll).symlink_to(self.path / "x32" / dll)

        self.wine_environment.dll_overrides.append("d3dx11_42=n")


@attrs.frozen
class SikarugirTemplateComponent(Component):
    wine: WineComponent
    render_backend: Literal["moltenvk", "kosmickrisp"]

    @override
    @property
    def path(self) -> Path:
        return super().path.parent / f"frameworks-{super().path.name}"

    @override
    def _extract(self, archive_path: Path, extract_dir: Path) -> Path:
        return super()._extract(archive_path, extract_dir) / "Contents"

    @override
    def inject(self) -> None:
        frameworks_path = self.path / "Frameworks"

        self.wine_environment.env_vars["DYLD_FALLBACK_LIBRARY_PATH"] = ":".join(
            str(path)
            for path in (
                (frameworks_path / "moltenvkcx"),
                (self.wine.path / "lib"),
                (self.wine.path / "lib64"),
                frameworks_path,
                "/opt/wine/lib",
                "/usr/lib",
                "/usr/libexec",
                "/usr/lib/system",
            )
        )

        driver_configs_path = self.path / "Resources/vulkan/icd.d"
        if driver_configs_path.exists():
            if self.render_backend == "moltenvk":
                self.wine_environment.env_vars["VK_DRIVER_FILES"] = str(
                    driver_configs_path / "MoltenVK_icd.json"
                )
            elif self.render_backend == "kosmickrisp":
                self.wine_environment.env_vars["VK_DRIVER_FILES"] = str(
                    driver_configs_path / "kosmickrisp_mesa_icd.json"
                )
            else:
                assert_never()

        # "wine doesn't handle VK_ERROR_DEVICE_LOST correctly"
        #     -- <https://github.com/Gcenx/macOS_Wine_builds/releases/tag/10.18>
        self.wine_environment.env_vars["MVK_CONFIG_RESUME_LOST_DEVICE"] = "1"

        if self.wine.wine_type == "sikarugir":
            self.wine_environment.env_vars["WINEDLLPATH_DXVK"] = str(
                self.path
                / f"SharedSupport/renderer/{
                    'dxvk3' if self.render_backend == 'kosmickrisp' else 'dxvk'
                }/wine"
            )
            if self.render_backend == "kosmickrisp":
                self.wine_environment.env_vars["DXVK_ASYNC"] = "1"
            # Used in older Sikarugir versions.
            self.wine_environment.env_vars["WINEDLLPATH_PREPEND"] = str(
                frameworks_path / "renderer/dxvk/wine"
            )


class WineManager:
    def __init__(self, wine_method: WineMethod | None) -> None:
        self.wine_environment: Final = WineEnvironment()
        self.wine_method: Final = wine_method or self.get_default_wine_method()

        # WINE:
        self._wine_10_linux = WineComponent(
            wine_environment=self.wine_environment,
            version="10.20-staging-tkg-amd64-wow64",
            url="https://github.com/Kron4ek/Wine-Builds/releases/download/10.20/wine-10.20-staging-tkg-amd64-wow64.tar.xz",
            wine_type="winehq",
            sha256_hash="1be498d2e0f1916d0cbe7f208ec6efe4fe2edab7c43f08e8ef006b04568474d9",
            compression_format="xztar",
        )
        self._wine_10_macos_sikarugir = WineComponent(
            wine_environment=self.wine_environment,
            version="WS12WineSikarugir10.0_6",
            url="https://github.com/Sikarugir-App/Engines/releases/download/v1.0/WS12WineSikarugir10.0_6.tar.xz",
            wine_type="sikarugir",
            sha256_hash="9da7ee0cbf386522f3a9906943726d9c3c125dbbd9ab120e3cde80e88d6091b2",
            compression_format="xztar",
        )
        self._wine_11_macos_sikarugir = WineComponent(
            wine_environment=self.wine_environment,
            version="WS11WineSikarugir11.0_1",
            url="https://github.com/Sikarugir-App/Engines/releases/download/v1.0/WS11WineSikarugir11.0_1.tar.xz",
            wine_type="sikarugir",
            sha256_hash="266e852bdb98e80da09f09d4ee10fd9fd3dbb6b18b0801c0836f1430c4979fb6",
            compression_format="xztar",
        )
        self._wine_11_macos = WineComponent(
            wine_environment=self.wine_environment,
            version="wine-stable-11.0_1-osx64",
            url="https://github.com/Gcenx/macOS_Wine_builds/releases/download/11.0_1/wine-stable-11.0_1-osx64.tar.xz",
            wine_type="winehq",
            sha256_hash="b50dc50ec7f41d58b115a6b685d4d1315ba3c797bd3aa0f49213f2703cb82388",
            compression_format="xztar",
        )

        # WINE Sikarugir templates:
        self._sikarugir_template_1_0_11 = partial(
            SikarugirTemplateComponent,
            wine_environment=self.wine_environment,
            version="Template-1.0.11",
            url="https://github.com/Sikarugir-App/Wrapper/releases/download/v1.0/Template-1.0.11.tar.xz",
            sha256_hash="9fa15479e7ff6abd99c1d07be285fb95f41fc6991586502427152b1f7d6ccb8a",
            compression_format="xztar",
        )
        self._sikarugir_template_1_0_27 = partial(
            SikarugirTemplateComponent,
            wine_environment=self.wine_environment,
            version="Template-1.0.27",
            url="https://github.com/Sikarugir-App/Template/releases/download/v1.0/Template-1.0.27.tar.xz",
            sha256_hash="dd0778f7b553d63df9b0f4e2cda3f3c6c005aabb75588c84d604afe80cdedbb9",
            compression_format="xztar",
        )

        # DXVK:
        self._dxvk_3_1 = DxvkComponent(
            wine_environment=self.wine_environment,
            version="3.1",
            url="https://github.com/doitsujin/dxvk/releases/download/v3.1/dxvk-3.1.tar.gz",
            sha256_hash="30f9cc326874be344285582275446968cfa4c069db31ce56df312d6644179154",
            compression_format="gztar",
        )
        self._dxvk_1_macos = DxvkComponent(
            wine_environment=self.wine_environment,
            version="1.10.3-20230507-repack",
            url="https://github.com/Gcenx/DXVK-macOS/releases/download/v1.10.3-20230507-repack/dxvk-macOS-async-v1.10.3-20230507-repack.tar.gz",
            sha256_hash="acd1520ad105d8ef124a09c8e11a259a5dc8bdc565ad18e0e52693f9807b2477",
            compression_format="gztar",
        )

        self._d3d_extras = D3dExtrasComponent(
            wine_environment=self.wine_environment,
            version="2",
            url="https://github.com/lutris/d3d_extras/releases/download/v2/v2.tar.xz",
            sha256_hash="9117ac86947b53865fc0d675314179e738b1e3e38bbb4281e4afe6b665b073af",
            compression_format="xztar",
        )

    def get_default_wine_method(self) -> WineMethod:
        if sys.platform == "darwin":
            if platform.machine() == "x86_64":
                return WineMethod.MOLTENVK_LEGACY
            else:
                return WineMethod.MOLTENVK_WINEHQ
        else:
            return WineMethod.LINUX

    @cached_property
    def components(self) -> tuple[Component, ...]:
        match self.wine_method:
            case WineMethod.LINUX:
                return (
                    self._wine_10_linux,
                    self._dxvk_3_1,
                    self._d3d_extras,
                )
            case WineMethod.MOLTENVK_WINEHQ:
                return (
                    self._wine_11_macos,
                    self._sikarugir_template_1_0_11(
                        wine=self._wine_11_macos, render_backend="moltenvk"
                    ),
                    self._dxvk_1_macos,
                    self._d3d_extras,
                )
            case WineMethod.MOLTENVK_LEGACY:
                return (
                    self._wine_10_macos_sikarugir,
                    self._sikarugir_template_1_0_11(
                        wine=self._wine_10_macos_sikarugir, render_backend="moltenvk"
                    ),
                    self._d3d_extras,
                )
            case WineMethod.MOLTENVK:
                return (
                    self._wine_11_macos_sikarugir,
                    self._sikarugir_template_1_0_27(
                        wine=self._wine_11_macos_sikarugir, render_backend="moltenvk"
                    ),
                    self._d3d_extras,
                )
            case WineMethod.KOSMICKRISP:
                return (
                    self._wine_11_macos_sikarugir,
                    self._sikarugir_template_1_0_27(
                        wine=self._wine_11_macos_sikarugir, render_backend="kosmickrisp"
                    ),
                    self._d3d_extras,
                )

            case _:
                assert_never(self.wine_method)

    @property
    def wine_component(self) -> WineComponent:
        return next(
            component
            for component in self.components
            if isinstance(component, WineComponent)
        )

    async def setup(self, progress: Progress) -> None:
        """
        Raises:
            WineComponentDownloadError
        """
        logger.info("Setting up WINE components")
        logger.debug("Components: %s", self.components)

        self.wine_environment.downloads_path.mkdir(parents=True, exist_ok=True)
        self.wine_environment.create_prefix()

        components_to_download = tuple(
            component for component in self.components if not component.is_downloaded
        )
        logger.debug("Components to download: %s", components_to_download)

        # Re-create prefix if component versions change.
        if components_to_download:
            rmtree(self.wine_environment.prefix_path)
            self.wine_environment.create_prefix()

        # Remove old component versions.
        component_paths = tuple(
            trio.Path(component.path) for component in self.components
        )
        for path in await trio.Path(self.wine_environment.downloads_path).iterdir():
            if path not in component_paths:
                if await path.is_file():
                    await path.unlink()
                else:
                    await trio.to_thread.run_sync(rmtree, str(path))

        try:
            async with trio.open_nursery() as nursery:
                for component in components_to_download:
                    nursery.start_soon(component.download, progress)
        except* (HTTPError, HashMismatchError) as e:
            raise WineComponentDownloadError() from e

        for component in self.components:
            component.inject()


def ensure_rosetta(wine_binary: Path | str) -> None:
    if sys.platform == "darwin":
        try:
            subprocess.run(  # noqa: S603
                [wine_binary, "--version"],
                check=True,
            )
        except OSError as e:
            if e.errno != errno.EBADARCH:
                raise e

            show_warning_message(
                dedent("""
                It looks like Rosetta wasn't automatically installed.
                Follow these directions to install it:

                1. Open the Terminal. It is in the Utilities folder in your Applications folder.

                2. Type or paste the following command in the Terminal:

                    - `softwareupdate --install-rosetta`

                3. Press Return and follow the on-screen instructions.

                See <https://support.apple.com/en-us/102527> for more information.
                """),
                get_qapp().activeWindow(),
                markdown=True,
            )
            ensure_rosetta(wine_binary=wine_binary)
    else:
        logger.warning("`ensure_rosetta` called outside of macOS")
        return


class WineSetupDialog(QtWidgets.QProgressDialog):
    def __init__(self, progress: Progress) -> None:
        self.progress = progress

        super().__init__(
            "Setting up WINE...",
            "",
            0,
            100,
            get_qapp().activeWindow(),
            QtCore.Qt.WindowType.FramelessWindowHint,
        )
        self.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        self.setMinimumSize(250, 80)
        self.setCancelButton(None)
        self.progress_bar = QtWidgets.QProgressBar(self)
        self.setBar(self.progress_bar)

    async def run(self) -> None:
        try:
            self.show()
            while True:
                self.update_progress_bar()
                await trio.sleep(0.05)
        finally:
            self.close()

    def update_progress_bar(self) -> None:
        current_progress = self.progress.get_current_progress()
        # Show busy indicator when downloading is done and extraction is still
        # happening.
        if current_progress.completed == current_progress.total:
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(0)
        else:
            self.progress_bar.setFormat(current_progress.progress_text)
            self.progress_bar.setMaximum(current_progress.total)
            self.progress_bar.setValue(current_progress.completed)


async def get_wine_process_args(
    command: tuple[str | Path, ...],
    environment: MappingProxyType[str, str],
    wine_config: WineConfigSection,
) -> tuple[tuple[str | Path, ...], MappingProxyType[str, str]]:
    """
    Configure `run_process` arguments to use WINE.

    Raises:
        WineComponentDownloadError
    """
    if os.name == "nt":
        logger.warning("Attempt to use WINE on Windows. No changes were made.")
        return command, environment

    edited_environment = environment.copy()

    if wine_config.builtin_prefix_enabled:
        wine_manager = WineManager(wine_config.wine_method)
        progress = Progress(unit_type="byte")
        async with trio.open_nursery() as nursery:
            if any(
                not component.is_downloaded for component in wine_manager.components
            ):
                wine_setup_dialog = WineSetupDialog(progress)
                nursery.start_soon(wine_setup_dialog.run)
            await wine_manager.setup(progress)
            nursery.cancel_scope.cancel()

        edited_environment.update(wine_manager.wine_environment.env_vars)
        edited_environment["WINEDLLOVERRIDES"] = ";".join(
            wine_manager.wine_environment.dll_overrides
        )
        wine_bin = str(wine_manager.wine_component.binary_path)
    else:
        if wine_config.user_prefix_path:
            edited_environment["WINEPREFIX"] = str(wine_config.user_prefix_path)
        wine_bin = (
            str(wine_config.user_wine_executable_path)
            if wine_config.user_wine_executable_path
            else "wine"
        )

    if sys.platform == "darwin" and platform.machine() != "x86_64":
        ensure_rosetta(wine_binary=wine_bin)

    edited_environment["WINEDEBUG"] = wine_config.debug_level or "-all"
    if "DXVK_LOG_LEVEL" not in edited_environment:
        edited_environment["DXVK_LOG_LEVEL"] = "error"

    return ((wine_bin, *command), MappingProxyType(edited_environment))
