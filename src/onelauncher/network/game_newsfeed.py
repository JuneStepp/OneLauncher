import calendar
import html
import logging
from datetime import datetime
from io import StringIO

import feedparser
from babel import Locale
from babel.dates import format_datetime
from PySide6 import QtCore, QtWidgets

from .httpx_client import get_httpx_client


async def newsfeed_url_to_html(url: str, babel_locale: Locale) -> str:
    """
    Raises:
        HTTPError: Network error while downloading newsfeed
    """
    response = await get_httpx_client(url).get(url)
    response.raise_for_status()

    return newsfeed_xml_to_html(response.text, babel_locale, url)


def _escape_feed_val(details: feedparser.util.FeedParserDict) -> str:
    """Return escaped value if the type is 'text/plain'. Otherwise, return the original value.
        See https://github.com/kurtmckee/feedparser/blame/b6917f83354a58348a16cf1106d64ea6622e24df/docs/html-sanitization.rst#L24-L31
        Summary is that values marked as 'text/plain' aren't sanitized.
    Args:
        details (feedparser.util.FeedParserDict): Value details dict. Ex. entry.title_detail
    """
    if details["type"] != "text/plain":
        return details["value"]

    return html.escape(details["value"])


def newsfeed_xml_to_html(
    newsfeed_string: str, babel_locale: Locale, original_feed_url: str | None = None
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
                datetime_object, format="medium", locale=babel_locale
            )
        else:
            date = ""
        entry_url = entry.get("link", "")

        # Make sure description doesn't have extra padding
        description = description.strip()
        description = description.removeprefix("<p>")
        description = description.removesuffix("</p>")

        qapp: QtWidgets.QApplication = qApp  # type: ignore[name-defined]  # noqa: F821
        entries_html += f"""
        <div>
            <h4 style="margin: 0; margin-bottom: 0.2em; font-weight: 600">
                <a href="{entry_url}" style="color: {"#ffd100" if qapp.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark else "#be9b00"}; text-decoration: none">
                    {title}
                </a>
            </h4>
            
            <small align="right">
                <i>{date}</i>
            </small>

            <p style="margin: 0; margin-top:0.25em">{description}</p>
        </div>
        <hr style="margin: 0; margin-top: 0.35em"/>
        """

    feed_url = feed_dict.feed.get("link") or original_feed_url
    return f"""
    <html>
        <body>
            <div style="width:auto">
                {entries_html}
                <div align="center">
                    <a href="{feed_url or ""}">
                        {"..." if feed_url else ""}
                    </a>
                </div>
            </div>
        </body>
    </html>
    """


logger = logging.getLogger("main")
