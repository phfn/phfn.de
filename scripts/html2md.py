#!/usr/bin/env python3
"""Convert HTML from stdin to Markdown on stdout.

Pure stdlib, no dependencies. Usage:
    cat page.html | ./scripts/html2md.py
    curl -s https://example.com | ./scripts/html2md.py
"""
import re
import sys
from html.parser import HTMLParser

BLOCK = {
    "p", "div", "section", "article", "header", "footer", "main",
    "aside", "nav", "figure", "figcaption", "table", "tr", "ul", "ol",
}
SKIP = {"script", "style", "head", "title", "meta", "link", "noscript"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}


def slugify(text):
    """Reproduce Hugo/goldmark auto heading IDs (e.g. "Präambel" -> "präambel")."""
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"[^\w\-]", "", text, flags=re.UNICODE)
    return text


def build_anchor_map(html):
    """Map original heading ids to the slug Hugo will generate for them."""

    class Collector(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.map = {}
            self.cur_id = None
            self.buf = []

        def handle_starttag(self, tag, attrs):
            if tag in HEADINGS:
                self.cur_id = dict(attrs).get("id")
                self.buf = []

        def handle_data(self, data):
            if self.cur_id is not None:
                self.buf.append(data)

        def handle_endtag(self, tag):
            if tag in HEADINGS and self.cur_id is not None:
                self.map[self.cur_id] = slugify("".join(self.buf))
                self.cur_id = None

    collector = Collector()
    collector.feed(html)
    return collector.map


class Html2Md(HTMLParser):
    def __init__(self, anchors=None):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.list_stack = []
        self.href = None
        self.pre = False
        self.in_code = False
        self.anchors = anchors or {}

    def emit(self, text):
        self.out.append(text)

    def last_char(self):
        text = "".join(self.out)
        return text[-1] if text else ""

    def at_line_start(self):
        text = "".join(self.out)
        return text == "" or text.endswith("\n")

    def close_inline(self, marker):
        text = "".join(self.out)
        stripped = text.rstrip(" \t")
        trailing = text[len(stripped):]
        if trailing:
            self.out = [stripped]
            self.emit(marker)
            self.emit(trailing)
        else:
            self.emit(marker)

    def newline(self, count=1):
        text = "".join(self.out)
        stripped = text.rstrip("\n")
        trailing = len(text) - len(stripped)
        if trailing < count:
            self.out.append("\n" * (count - trailing))

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        attrs = dict(attrs)
        if tag in HEADINGS:
            self.newline(2)
            self.emit("#" * int(tag[1]) + " ")
        elif tag == "p":
            self.newline(2)
        elif tag == "br":
            self.emit("  \n")
        elif tag == "hr":
            self.newline(2)
            self.emit("---")
            self.newline(2)
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
        elif tag == "code" and not self.pre:
            self.emit("`")
            self.in_code = True
        elif tag == "pre":
            self.newline(2)
            self.emit("```\n")
            self.pre = True
        elif tag == "blockquote":
            self.newline(2)
            self.emit("> ")
        elif tag == "a":
            href = attrs.get("href")
            if href and href.startswith("#"):
                href = "#" + self.anchors.get(href[1:], href[1:])
            self.href = href
            self.emit("[")
        elif tag == "img":
            src = attrs.get("src", "")
            alt = attrs.get("alt", "")
            self.emit(f"![{alt}]({src})")
        elif tag in ("ul", "ol"):
            self.newline(2)
            self.list_stack.append([tag, 0])
        elif tag == "li":
            self.newline()
            if self.list_stack:
                kind, n = self.list_stack[-1]
                if kind == "ol":
                    n += 1
                    self.list_stack[-1][1] = n
                    self.emit(f"{n}. ")
                else:
                    self.emit("- ")
        elif tag in BLOCK:
            self.newline(2)

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag in HEADINGS:
            self.newline(2)
        elif tag == "p":
            self.newline(2)
        elif tag in ("strong", "b"):
            self.close_inline("**")
        elif tag in ("em", "i"):
            self.close_inline("*")
        elif tag == "code" and not self.pre:
            self.emit("`")
            self.in_code = False
        elif tag == "pre":
            self.newline()
            self.emit("```")
            self.pre = False
            self.newline(2)
        elif tag == "a":
            href = self.href or ""
            self.emit(f"]({href})")
            self.href = None
        elif tag in ("ul", "ol"):
            if self.list_stack:
                self.list_stack.pop()
            self.newline(2)
        elif tag == "li":
            self.newline()
        elif tag in BLOCK:
            self.newline(2)

    def handle_data(self, data):
        if self.skip_depth:
            return
        if self.pre:
            self.emit(data)
            return
        text = " ".join(data.split())
        if text:
            if data[:1].isspace() and not self.at_line_start() and self.last_char() not in (" ", "\t"):
                text = " " + text
            if data[-1:].isspace():
                text = text + " "
            self.emit(text)
        elif data and not self.at_line_start() and self.last_char() not in (" ", "\t", "\n"):
            self.emit(" ")

    def result(self):
        text = "".join(self.out)
        lines = []
        for raw in text.splitlines():
            hard = raw.endswith("  ")
            ln = raw.rstrip(" \t")
            if ln and hard:
                ln = ln + "  "
            lines.append(ln)
        cleaned = []
        blank = 0
        for ln in lines:
            if ln == "":
                blank += 1
                if blank > 1:
                    continue
            else:
                blank = 0
            cleaned.append(ln)
        return "\n".join(cleaned).strip() + "\n"


def main():
    html = sys.stdin.read()
    parser = Html2Md(anchors=build_anchor_map(html))
    parser.feed(html)
    parser.close()
    sys.stdout.write(parser.result())


if __name__ == "__main__":
    main()
