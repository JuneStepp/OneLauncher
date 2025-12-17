from pathlib import Path
from typing import Any, Final, Literal, Self

import attrs
import xmlschema
from asyncache import cached as async_cached
from cachetools import TTLCache

from onelauncher.network.httpx_client import get_httpx_client
from onelauncher.resources import data_dir

_PATCHING_FILE_LIST_SCHEMA: Final = xmlschema.XMLSchema(
    source=data_dir / "network" / "schemas" / "akamai_patching_file_list.xsd"
)
_SPLASHSCREEN_FILE_LIST_SCHEMA: Final = xmlschema.XMLSchema(
    data_dir / "network" / "schemas" / "splashscreen_file_list.xsd"
)


@attrs.frozen(kw_only=True)
class PatchingDownloadFile:
    relative_url: str
    relative_path: Path
    size: int
    """bytes"""
    md5_hash: str


@attrs.frozen(kw_only=True)
class PatchingDownloadList:
    download_files: tuple[PatchingDownloadFile, ...]

    @classmethod
    @async_cached(cache=TTLCache(maxsize=1, ttl=60 * 5))
    async def get_from_url(cls: type[Self], url: str) -> Self:
        """
        Raises:
            HTTPError: Network error while downloading the file list
            XMLSchemaValidationError: File list doesn't match schema
        """
        response = await get_httpx_client(url).get(url)
        response.raise_for_status()

        file_list_dict: dict[Literal["File"], Any] = _PATCHING_FILE_LIST_SCHEMA.to_dict(  # type: ignore[assignment]
            response.text
        )
        return cls(
            download_files=tuple(
                PatchingDownloadFile(
                    relative_url=file_dict["From"].replace("\\", "/"),
                    relative_path=Path(file_dict["To"].replace("\\", "/")),
                    size=file_dict["Size"],
                    md5_hash=file_dict["MD5"],
                )
                for file_dict in file_list_dict["File"]
            )
        )


@attrs.frozen(kw_only=True)
class SplashscreenDownloadFile:
    url: str
    description: str
    relative_path: Path


@attrs.frozen(kw_only=True)
class SplashscreenDownloadList:
    download_files: tuple[SplashscreenDownloadFile, ...]

    @classmethod
    @async_cached(cache=TTLCache(maxsize=1, ttl=60 * 5))
    async def get_from_url(cls: type[Self], url: str) -> Self:
        """
        Raises:
            HTTPError: Network error while downloading the file list
            XMLSchemaValidationError: File list doesn't match schema
        """
        response = await get_httpx_client(url).get(url)
        response.raise_for_status()

        file_list_dict: dict[Literal["File"], Any] = (
            _SPLASHSCREEN_FILE_LIST_SCHEMA.to_dict(  # type: ignore[assignment]
                response.text
            )
        )
        return cls(
            download_files=tuple(
                SplashscreenDownloadFile(
                    url=file_dict["DownloadUrl"],
                    description=file_dict["Description"],
                    relative_path=Path(file_dict["FileName"].replace("\\", "/")),
                )
                for file_dict in file_list_dict["File"]
            )
        )
