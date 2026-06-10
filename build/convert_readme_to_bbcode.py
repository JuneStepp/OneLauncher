from __future__ import annotations

from html.parser import HTMLParser
from typing import cast, override
from urllib.parse import urlparse, urlunparse

import marko

from onelauncher.__about__ import __project_url__


class HTMLToBBCodeParser(HTMLParser):
    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.attrs:
            self.attrs[tag] = []

        attrs_dict: dict[str, str | None] = dict(attrs)
        if tag == "p" and attrs_dict.get("align") == "center":
            self.data.append("[CENTER]")
            self.attrs[tag].append(attrs_dict)
        elif tag == "a":
            self.data.append(f"[URL={attrs_dict.get('href', '')}]")
        elif tag == "img":
            self.data.append(f"[IMG]{attrs_dict.get('src', '')}")
        elif tag == "span":
            return
        else:
            string_attrs = "".join(
                f" {key}={value}" for key, value in attrs_dict.items()
            )
            self.data.append(f"<{tag}{string_attrs}>")

    @override
    def handle_endtag(self, tag: str) -> None:
        if self.attrs.get(tag):
            attrs = self.attrs[tag][-1]
            if attrs.get("align") == "center":
                self.data.append("[/CENTER]")

            del self.attrs[tag][-1]
        elif tag == "a":
            self.data.append("[/URL]")
        elif tag == "img":
            self.data.append("[/IMG]")
        elif tag == "span":
            return
        else:
            self.data.append(f"</{tag}>")

    @override
    def handle_data(self, data: str) -> None:
        self.data.append(data)

    @override
    def handle_comment(self, data: str) -> None:
        """Don't render comments"""
        return

    def get_bbcode(self, data: str) -> str:
        self.attrs: dict[str, list[dict[str, str | None]]] = {}
        self.data: list[str] = []
        super().feed(data)
        return "".join(self.data)


class BBCodeRenderer(marko.renderer.Renderer):
    """Render as LotroInterface and NexusMods compatible BBCode"""

    html_parser = HTMLToBBCodeParser()
    parsed_github_project_url = urlparse(__project_url__)

    def render_paragraph(self, element: marko.block.Paragraph) -> str:
        children = self.render_children(element)
        return f"{children}\n"

    def render_list(self, element: marko.block.List) -> str:
        return f"[LIST{'=1' if element.ordered else ''}]\n{self.render_children(element)}[/LIST]"

    def render_list_item(self, element: marko.block.ListItem) -> str:
        return f"[*]{self.render_children(element)}"

    def render_quote(self, element: marko.block.Quote) -> str:
        return f"[QUOTE]\n{self.render_children(element)}</QUOTE>\n"

    def render_fenced_code(self, element: marko.block.FencedCode) -> str:
        return f"[CODE]{self.render_children(element)}[/CODE]\n"  # type

    def render_code_block(self, element: marko.block.CodeBlock) -> str:
        return self.render_fenced_code(cast(marko.block.FencedCode, element))

    def render_html_block(self, element: marko.block.HTMLBlock) -> str:
        return self.html_parser.get_bbcode(element.body)

    def render_thematic_break(self, element: marko.block.ThematicBreak) -> str:
        return ""

    def render_heading(self, element: marko.block.Heading) -> str:
        bbcode_size = max(7 - element.level, 1)
        return f"[SIZE={bbcode_size}][B]{self.render_children(element)}[/B][/SIZE]\n"

    def render_setext_heading(self, element: marko.block.SetextHeading) -> str:
        return self.render_heading(cast(marko.block.Heading, element))

    def render_blank_line(self, element: marko.block.BlankLine) -> str:
        return "\n"

    def render_link_ref_def(self, element: marko.block.LinkRefDef) -> str:
        return f"[URL={element.dest}]{element.title or element.dest}[/URL]"

    def render_emphasis(self, element: marko.inline.Emphasis) -> str:
        return f"[I]{self.render_children(element)}[/I]"

    def render_strong_emphasis(self, element: marko.inline.StrongEmphasis) -> str:
        return f"[B]{self.render_children(element)}[/B]"

    def render_inline_html(self, element: marko.inline.InlineHTML) -> str:
        return cast(str, element.children)

    def render_link(self, element: marko.inline.Link) -> str:
        dest = element.dest
        parsed_dest = urlparse(element.dest)
        if not parsed_dest.scheme and not parsed_dest.netloc:
            dest = urlunparse(
                self.parsed_github_project_url._replace(
                    path=f"{self.parsed_github_project_url.path}{f'/blob/HEAD/{parsed_dest.path}' if parsed_dest.path else ''}",
                    fragment=parsed_dest.fragment,
                )
            )
        return f"[URL={dest}]{element.title or ''}{self.render_children(element)}[/URL]"

    def render_auto_link(self, element: marko.inline.AutoLink) -> str:
        return self.render_link(cast(marko.inline.Link, element))

    def render_image(self, element: marko.inline.Image) -> str:
        return f"[IMG]{element.dest}[/IMG]"

    def render_literal(self, element: marko.inline.Literal) -> str:
        return f"[NOPARSE]{element.children}[/NOPARSE]"

    def render_raw_text(self, element: marko.inline.RawText) -> str:
        return f"{element.children}"

    def render_line_break(self, element: marko.inline.LineBreak) -> str:
        return "\n" if element.soft else "\\\n"

    def render_code_span(self, element: marko.inline.CodeSpan) -> str:
        return f"[B][FONT=Courier New]{element.children}[/FONT][/B]"


def convert(readme_text: str) -> str:
    markdown_class = marko.Markdown(renderer=BBCodeRenderer)
    return markdown_class.convert(readme_text)
