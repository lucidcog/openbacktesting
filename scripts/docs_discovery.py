"""Publish portable Markdown and search metadata from the same rendered manual."""

from __future__ import annotations

import html
import os
import posixpath
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit, urlunsplit

from mkdocs.exceptions import ConfigurationError
from mkdocs.utils import get_relative_url

FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)
LINK = re.compile(r"(?P<prefix>!?\[[^\]\n]*\]\()(?P<url>[^\s)]+)(?P<suffix>\))")
REFERENCE = re.compile(r"^(?P<prefix> {0,3}\[[^\]\n]+\]:\s*)(?P<url>\S+)", re.MULTILINE)
HTML_LINK = re.compile(r'(?P<prefix>\b(?:href|src)=["\'])(?P<url>[^"\']+)(?P<suffix>["\'])')
_serving = False
_pages = {}


class PageText(HTMLParser):
    """Extract a real heading and opening prose without code or permalink symbols."""

    def __init__(self):
        super().__init__()
        self.heading = []
        self.paragraphs = []
        self.current = None
        self.prose = []
        self.links = 0
        self.in_heading = False
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.skip or tag in {"pre", "script", "style"} or attrs.get("class") == "headerlink":
            self.skip += 1
        elif tag == "h1" and not self.heading:
            self.in_heading = True
        elif tag == "p":
            self.current = []
            self.prose = []
        elif tag == "a":
            self.links += 1

    def handle_endtag(self, tag):
        if self.skip:
            self.skip -= 1
        elif tag == "h1":
            self.in_heading = False
        elif tag == "a":
            self.links = max(0, self.links - 1)
        elif tag == "p" and self.current is not None:
            value = "".join(self.current).strip()
            if value and re.search(r"\w{3,}", "".join(self.prose)):
                self.paragraphs.append(value)
            self.current = None

    def handle_data(self, data):
        if not self.skip:
            if self.in_heading:
                self.heading.append(data)
            if self.current is not None:
                self.current.append(data)
                if not self.links:
                    self.prose.append(data)


def plain(value):
    return " ".join(value.split())


def summary(value, limit=180):
    value = plain(value)
    return value if len(value) <= limit else value[: limit - 1].rsplit(" ", 1)[0] + "…"


def markdown_path(file):
    """A directory page /guide/ exposes its Markdown at /guide/index.md."""
    return str(Path(file.dest_uri).with_suffix(".md")).replace(os.sep, "/")


def portable_markdown(markdown, page, files, site_url):
    """Make links portable while preserving every fenced executable example."""

    def absolute(url):
        parts = urlsplit(html.unescape(url))
        if parts.scheme or parts.netloc:
            return url
        if not parts.path:
            return urljoin(site_url, page.file.url) + url
        uri = posixpath.normpath(
            posixpath.join(posixpath.dirname(page.file.src_uri), unquote(parts.path))
        )
        target = files.get_file_from_path(uri)
        if target:
            path = markdown_path(target) if target.is_documentation_page() else target.url
            return urlunsplit((*urlsplit(urljoin(site_url, path))[:3], parts.query, parts.fragment))
        # Root-relative URLs already name a published resource, not a source file.
        return urljoin(urljoin(site_url, page.file.url), url)

    def rewrite(match):
        return match["prefix"] + absolute(match["url"]) + (match.groupdict().get("suffix") or "")

    def prose(value):
        value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
        return HTML_LINK.sub(rewrite, REFERENCE.sub(rewrite, LINK.sub(rewrite, value)))

    output, start = [], 0
    for fence in FENCE.finditer(markdown):
        output.extend([prose(markdown[start : fence.start()]), fence[0]])
        start = fence.end()
    output.append(prose(markdown[start:]))
    return "".join(output).strip() + "\n"


def on_startup(command, dirty):
    global _serving
    _serving = command == "serve"


def on_config(config):
    _pages.clear()
    parts = urlsplit(config.site_url or "")
    if not parts.netloc or parts.query or parts.fragment or parts.username is not None:
        raise ConfigurationError(
            "site_url must be an absolute documentation URL without credentials, query, or fragment."
        )
    if not _serving and parts.scheme != "https":
        raise ConfigurationError("Published documentation requires an HTTPS site_url.")
    config.site_url = config.site_url.rstrip("/") + "/"
    environment = os.environ.get("DOCS_ENV", "")
    if environment not in {"", "production", "preview"}:
        raise ConfigurationError("DOCS_ENV must be production or preview.")
    preview = (
        _serving
        or environment == "preview"
        or (os.environ.get("CF_PAGES") == "1" and environment != "production")
    )
    config.extra["docs_indexable"] = not preview
    return config


def on_page_content(content, page, config, files):
    text = PageText()
    text.feed(content)
    title = plain("".join(text.heading)) or page.title
    page.meta.setdefault("title", title)
    description = next(iter(text.paragraphs), title)
    page.meta.setdefault("description", summary(description or title))
    indexable = config.extra["docs_indexable"] and not page.file.src_uri.startswith("repository/")
    raw_path = markdown_path(page.file)
    page.meta["discovery"] = {
        "indexable": indexable,
        "markdown": get_relative_url(raw_path, page.file.url),
        "markdown_url": urljoin(config.site_url, raw_path),
    }
    _pages[page.file.src_uri] = {
        "page": page,
        "markdown": portable_markdown(page.markdown, page, files, config.site_url),
        "path": raw_path,
    }
    return content


def on_page_context(context, page, config, nav):
    crumbs = []
    if not page.is_homepage:
        crumbs.append({"title": "OpenBacktesting", "url": config.site_url})
        directories = Path(page.file.src_uri).parents
        for directory in reversed(directories):
            key = (directory / "index.md").as_posix()
            parent = _pages.get(key)
            if parent and key not in {"index.md", page.file.src_uri}:
                parent_page = parent["page"]
                crumbs.append(
                    {"title": parent_page.meta["title"], "url": parent_page.canonical_url}
                )
    crumbs.append({"title": page.meta["title"], "url": page.canonical_url})
    discovery = page.meta["discovery"]
    discovery["breadcrumbs"] = [
        {
            **item,
            "href": get_relative_url(
                urlsplit(item["url"]).path.removeprefix(urlsplit(config.site_url).path),
                page.file.url,
            ),
        }
        for item in crumbs
    ]
    website = {
        "@type": "WebSite",
        "@id": config.site_url + "#website",
        "url": config.site_url,
        "name": config.site_name,
    }
    article = {
        "@type": "TechArticle",
        "@id": page.canonical_url + "#article",
        "url": page.canonical_url,
        "headline": page.meta["title"],
        "description": page.meta["description"],
        "inLanguage": "en",
        "isPartOf": {"@id": website["@id"]},
        "mainEntityOfPage": page.canonical_url,
        "publisher": {"@type": "Organization", "name": "LucidCog", "url": "https://lucidcog.com"},
    }
    graph = [website, article]
    if len(crumbs) > 1:
        graph.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "name": item["title"], "item": item["url"]}
                    for i, item in enumerate(crumbs, 1)
                ],
            }
        )
    discovery["schema"] = {"@context": "https://schema.org", "@graph": graph}
    return context


def on_post_build(config):
    destination = Path(config.site_dir)
    for record in _pages.values():
        path = destination / record["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(record["markdown"], encoding="utf-8")

    sections = {"Start here": [], "Guides": [], "API reference": [], "Optional": []}
    full = ["# OpenBacktesting documentation\n"]
    priority = {"index.md": 0, "quickstart.md": 1, "examples.md": 2, "limitations.md": 3}
    for uri, record in sorted(_pages.items(), key=lambda item: (priority.get(item[0], 4), item[0])):
        page = record["page"]
        if uri.startswith("repository/") and not uri.startswith("repository/examples/"):
            continue
        full.append(f"\n---\n\nSource: {page.canonical_url}\n\n{record['markdown']}")
        if uri.startswith("reference/indicators/") and uri != "reference/indicators/index.md":
            continue
        if uri.startswith("repository/"):
            continue
        section = (
            "Start here"
            if uri in {"index.md", "quickstart.md", "examples.md", "limitations.md"}
            else "Guides"
            if uri.startswith("guides/")
            else "API reference"
            if uri.startswith("reference/")
            else "Optional"
        )
        sections[section].append(
            f"- [{page.meta['title']}]({page.meta['discovery']['markdown_url']}): {page.meta['description']}\n"
        )
    intro = (
        "# OpenBacktesting\n\n"
        "> Python framework for historical, bar-by-bar backtesting with indicators, orders, trades, optimization, and portfolio reports.\n\n"
        "Each run models one asset and one settlement currency. The package exports plotting data but does not include a chart renderer or live-trading connection. "
        "Read the quickstart and limitations before adapting examples. Indicators may be invalid during warmup; check validity before using values.\n\n"
        "Follow the Markdown links below. The indicator catalog links to each indicator's parameters, outputs, and runnable example.\n"
    )
    sections["Optional"].extend(
        [
            f"- [Full documentation]({urljoin(config.site_url, 'llms-full.txt')}): Combined manual and runnable example sources; large context.\n",
            f"- [Sitemap]({urljoin(config.site_url, 'sitemap.xml')}): Canonical HTML documentation URLs.\n",
        ]
    )
    index = intro + "".join(
        f"\n## {title}\n\n" + "".join(links) for title, links in sections.items()
    )
    for name in ("llms.txt", "llm.txt"):
        (destination / name).write_text(index, encoding="utf-8")
    (destination / "llms-full.txt").write_text("".join(full), encoding="utf-8")
    robots = "User-agent: *\nAllow: /\n"
    if config.extra["docs_indexable"]:
        robots += f"\nSitemap: {urljoin(config.site_url, 'sitemap.xml')}\n"
    (destination / "robots.txt").write_text(robots, encoding="utf-8")
    prefix = urlsplit(config.site_url).path
    headers = (
        "/*.md\n  Content-Type: text/markdown; charset=utf-8\n  X-Robots-Tag: noindex\n"
        f"{prefix}llms*.txt\n  Content-Type: text/plain; charset=utf-8\n  X-Robots-Tag: noindex\n"
        f"{prefix}llm.txt\n  Content-Type: text/plain; charset=utf-8\n  X-Robots-Tag: noindex\n"
        f"{prefix}404.html\n  X-Robots-Tag: noindex\n"
        "https://:project.pages.dev/*\n  X-Robots-Tag: noindex\n"
        "https://:version.:project.pages.dev/*\n  X-Robots-Tag: noindex\n"
    )
    if not config.extra["docs_indexable"]:
        headers += "/*\n  X-Robots-Tag: noindex\n"
    (destination / "_headers").write_text(headers, encoding="utf-8")
