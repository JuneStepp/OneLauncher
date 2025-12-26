import calendar
import html
import logging
from datetime import datetime
from io import StringIO
from typing import assert_never

import feedparser
from babel.dates import format_datetime
from PySide6 import QtCore

from onelauncher.game_config import GameConfig, GameType
from onelauncher.official_clients import (
    DDO_PREVIEW_LATEST_INFO_URL,
    LOTRO_PREVIEW_LATEST_INFO_URL,
    is_official_game_server,
)
from onelauncher.resources import OneLauncherLocale
from onelauncher.ui.qtapp import get_qapp

from .httpx_client import get_httpx_client

logger = logging.getLogger(__name__)


async def get_game_newsfeed_html(
    url: str, locale: OneLauncherLocale, game_config: GameConfig
) -> str:
    """
    Raises:
        HTTPError: Network error while downloading newsfeed
    """
    response = await get_httpx_client(url).get(url)
    response.raise_for_status()

    return newsfeed_xml_to_html(
        newsfeed_string=response.text,
        locale=locale,
        game_config=game_config,
        original_feed_url=url,
    )


def _escape_feed_val(details: feedparser.util.FeedParserDict) -> str:  # type: ignore[no-any-unimported]
    """Return escaped value if the type is 'text/plain'. Otherwise, return the original value.
        See https://github.com/kurtmckee/feedparser/blame/b6917f83354a58348a16cf1106d64ea6622e24df/docs/html-sanitization.rst#L24-L31
        Summary is that values marked as 'text/plain' aren't sanitized.
    Args:
        details (feedparser.util.FeedParserDict): Value details dict. Ex. entry.title_detail
    """
    details_val: str = details["value"]
    if details["type"] != "text/plain":
        return details_val

    return html.escape(details_val)


def get_newsfeed_css() -> str:
    news_entry_header_color = (
        "#ffd100"
        if get_qapp().styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark
        else "#be9b00"
    )
    return f"""
.news-entry-header {{
    margin: 0;
    margin-bottom: 0.2em;
    font-weight: 600;
    color: {news_entry_header_color};
}}
.news-entry-header a {{
    text-decoration: none;
    color: {news_entry_header_color};
}}
.news-entry-content {{
    margin: 0;
    margin-top:0.25em;
}}
.news-entries-break {{
    margin: 0;
    margin-top: 0.35em;
}}
"""


def newsfeed_xml_to_html(
    newsfeed_string: str,
    locale: OneLauncherLocale,
    game_config: GameConfig,
    original_feed_url: str,
) -> str:
    with StringIO(initial_value=newsfeed_string) as feed_text_stream:
        feed_dict = feedparser.parse(feed_text_stream.getvalue())

    entries_html = ""
    for entry in feed_dict.entries:
        title = (
            _escape_feed_val(entry["title_detail"]) if "title_detail" in entry else ""
        )
        description = (
            _escape_feed_val(entry["description_detail"])
            if "description_detail" in entry
            else ""
        )
        if "published_parsed" in entry:
            timestamp = calendar.timegm(entry["published_parsed"])
            datetime_object = datetime.fromtimestamp(timestamp)
            date = format_datetime(
                datetime_object, format="medium", locale=locale.babel_locale
            )
        else:
            date = ""
        entry_url = entry.get("link", "")

        # Make sure description doesn't have extra padding
        description = description.strip()
        description = description.removeprefix("<p>")
        description = description.removesuffix("</p>")

        entries_html += f"""
        <div>
            <h4 class="news-entry-header">
                <a href="{entry_url}">
                    {title}
                </a>
            </h4>
            
            <small align="right">
                <i>{date}</i>
            </small>

            <p class="news-entry-content">{description}</p>
        </div>
        <hr class="news-entries-break"/>
        """

    if game_config.game_type == GameType.LOTRO:
        preview_server_forums_url = LOTRO_PREVIEW_LATEST_INFO_URL
    elif game_config.game_type == GameType.DDO:
        preview_server_forums_url = DDO_PREVIEW_LATEST_INFO_URL
    else:
        assert_never()
    preview_server_status_message = f"""
        <div>
            <p>
                Go to <a href="{preview_server_forums_url}">the forums</a> for the
                latest info. This feed can be out of date.
            </p>
        </div>
        <hr class="news-entries-break"/>
    """

    feed_url = feed_dict.feed.get("link") or original_feed_url
    return f"""
    <html>
        <body>
            <div style="width:auto">
                {preview_server_status_message if game_config.is_preview_client and is_official_game_server(original_feed_url) else ""}
                {entries_html}
                <div align="center">
                    <a href="{feed_url or ""}">{"..." if feed_url else ""}</a>
                </div>
            </div>
        </body>
    </html>
    """
