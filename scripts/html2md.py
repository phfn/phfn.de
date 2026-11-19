#!/usr/bin/env python3
"""Convert HTML from stdin to Markdown on stdout.

Pure stdlib, no dependencies. Usage:
    cat page.html | ./scripts/html2md.py
    curl -s https://example.com | ./scripts/html2md.py
"""
import sys
from html.parser import HTMLParser

BLOCK = {
    "p", "div", "section", "article", "header", "footer", "main",
    "aside", "nav", "figure", "figcaption", "table", "tr", "ul", "ol",
}
SKIP = {"script", "style", "head", "title", "meta", "link", "noscript"}


class Html2Md(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.list_stack = []
        self.href = None
        self.pre = False
        self.in_code = False

    def emit(self, text):
        self.out.append(text)

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
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.newline(2)
            hid = attrs.get("id")
            if hid:
                self.emit(f'<a id="{hid}"></a>\n\n')
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
            self.href = attrs.get("href")
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
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.newline(2)
        elif tag == "p":
            self.newline(2)
        elif tag in ("strong", "b"):
            self.emit("**")
        elif tag in ("em", "i"):
            self.emit("*")
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
        else:
            text = " ".join(data.split())
            if text:
                if data[:1].isspace():
                    text = " " + text
                if data[-1:].isspace():
                    text = text + " "
            self.emit(text)

    def result(self):
        text = "".join(self.out)
        lines = [ln.rstrip() for ln in text.splitlines()]
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
    parser = Html2Md()
    parser.feed(html)
    parser.close()
    sys.stdout.write(parser.result())


if __name__ == "__main__":
    main()
