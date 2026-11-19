import html
import logging
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any, ClassVar

import attrs
import retryhttp
import xmlschema

from onelauncher.network.httpx_client import get_httpx_client

from ..resources import data_dir
from .addon import AddonType, RemoteAddon

logger = logging.getLogger(__name__)


@attrs.frozen(kw_only=True)
class LotroInterfaceFeed:
    name: str
    addons_type: AddonType
    url: str

    LOTROINTERFACE_FEED_SCHEMA: ClassVar = xmlschema.XMLSchema(
        data_dir / "addons/schemas/lotrointerface_feed.xsd"
    )

    @staticmethod
    def unescape_lotrointerface_feed_unicode(escaped_string: str) -> str:
        """
        Convert feed escaped characters to Unicode characters. This shouold be used with
        strings that have already had the XML unescaped.

        Unicode characters in LotroInterface feeds are escaped with an ampersand followed
        by the Unicode character number. Ex. `&1088`.
        """
        return html.unescape(
            # Convert to HTML escape notation by adding `#`.
            re.sub(
                r"&(\d+);",
                lambda match: f"&#{match.group(1)};",
                escaped_string,
            )
        )

    @retryhttp.retry(reraise=True)
    async def fetch_remote_addons(self) -> Iterable[RemoteAddon]:
        """
        Raises:
            HTTPError: Feed downloading error.
            XMLSchemaValidationError: Schema validation error.
        """
        response = await get_httpx_client(self.url).get(self.url, timeout=10)
        response.raise_for_status()

        feed_dict: Any = self.LOTROINTERFACE_FEED_SCHEMA.to_dict(response.text)
        return (
            RemoteAddon(
                name=self.unescape_lotrointerface_feed_unicode(interface["UIName"])
                .replace("/", "-")
                .replace("\\", "-"),
                description=self.unescape_lotrointerface_feed_unicode(
                    interface["UIDescription"]
                ).strip(),
                author=self.unescape_lotrointerface_feed_unicode(
                    interface["UIAuthorName"]
                ),
                version=interface["UIVersion"] or "",
                addon_type=self.addons_type,
                interface_id=interface["UID"],
                download_url=interface["UIFileURL"],
                last_updated=datetime.fromtimestamp(interface["UIUpdated"], tz=UTC),
                downloads_count=interface["UIDownloads"],
                category=interface["UICategory"],
                download_archive_name=interface["UIFile"],
                download_size=interface["UISize"],
                download_md5_hash=interface.get("UIMD5"),
            )
            for interface in feed_dict["Ui"]
        )


LOTRO_PLUGINS_FEED = LotroInterfaceFeed(
    name="LotroInterface Plugins",
    addons_type="plugin",
    url="https://api.lotrointerface.com/fav/OneLauncher-Plugins.xml",
)
LOTRO_SKINS_FEED = LotroInterfaceFeed(
    name="LotroInterface Skins",
    addons_type="skin",
    url="https://api.lotrointerface.com/fav/OneLauncher-Themes.xml",
)
LOTRO_MUSIC_FEED = LotroInterfaceFeed(
    name="LotroInterface Music",
    addons_type="music",
    url="https://api.lotrointerface.com/fav/OneLauncher-Music.xml",
)
DDO_SKINS_FEED = LotroInterfaceFeed(
    name="LotroInterface DDO Skins",
    addons_type="skin",
    url="https://api.lotrointerface.com/fav/OneLauncher-Themes-DDO.xml",
)
