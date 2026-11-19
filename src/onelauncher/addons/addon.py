from datetime import datetime
from typing import Literal

import attrs

type AddonType = Literal["plugin", "music", "skin"]
type InterfaceID = int


@attrs.frozen(kw_only=True)
class Addon:
    name: str
    description: str
    author: str
    version: str
    addon_type: AddonType


@attrs.frozen(kw_only=True)
class RemoteAddon(Addon):
    interface_id: InterfaceID
    download_url: str
    last_updated: datetime
    downloads_count: int
    category: str
    download_archive_name: str
    download_size: int
    download_md5_hash: str | None = None

    @property
    def info_url(self) -> str:
        """Replaces "download" with "info" in download url to make info url

        An example is: https://www.lotrointerface.com/downloads/download1078-VitalTarget
                   to: https://www.lotrointerface.com/downloads/info1078-VitalTarget
        """
        return self.download_url.replace("/downloads/download", "/downloads/info")
