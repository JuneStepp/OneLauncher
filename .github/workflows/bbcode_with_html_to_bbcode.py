import sys
from html.parser import HTMLParser
from pathlib import Path


class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.attrs:
            self.attrs[tag] = []

        attrs_dict: dict[str, str | None] = dict(attrs)
        if tag == "p" and attrs_dict.get("align") == "center":
            self.data.append("[center]")
            self.attrs[tag].append(attrs_dict)
        elif tag == "a":
            self.data.append(f"[url={attrs_dict.get('href', '')}]")
        elif tag == "span":
            return
        else:
            string_attrs = "".join(
                f" {key}={value}" for key, value in attrs_dict.items()
            )
            self.data.append(f"<{tag}{string_attrs}>")

    def handle_endtag(self, tag: str) -> None:
        if self.attrs.get(tag):
            attrs = self.attrs[tag][-1]
            if attrs.get("align") == "center":
                self.data.append("[/center]")

            del self.attrs[tag][-1]
        elif tag == "a":
            self.data.append("[/url]")
        elif tag == "span":
            return
        else:
            self.data.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.data.append(data)

    def handle_comment(self, data: str) -> None:
        """Leave comments as they are."""
        self.data.append(f"<!--{data}-->")

    def feed(self, data: str):
        self.attrs: dict[str, list[dict[str, str]]] = {}
        self.data = []
        HTMLParser.feed(self, data)
        return "".join(self.data)


input_file = Path(sys.argv[1])
with input_file.open("r") as file:
    input_text = file.read()
    # Disable comments that will break parsing
    input_text = input_text.replace("<!--", "<\\!--")
    input_text = input_text.replace("-->", "--\\>")
    # Comment out code blocks
    input_text = input_text.replace("[code]", "<!--[code]")
    input_text = input_text.replace("[/code]", "[/code]-->")

parser = MyHTMLParser()
formated_text = parser.feed(input_text)
# Uncomment code blocks
formated_text = formated_text.replace("<!--[code]", "[code]")
formated_text = formated_text.replace("[/code]-->", "[/code]")
# Re-enable original comments
formated_text = formated_text.replace("<\\!--", "<!--")
formated_text = formated_text.replace("--\\>", "-->")

formated_text = formated_text.strip()

with input_file.open("w") as file:
    file.write(formated_text)
