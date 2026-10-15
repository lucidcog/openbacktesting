"""Validate the complete built site, not just individual metadata helpers."""

import gzip
import importlib.util
import json
import os
import subprocess
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree

import pytest

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://docs.openbacktesting.com/"
SPEC = importlib.util.spec_from_file_location("docs_discovery", ROOT / "scripts/docs_discovery.py")
discovery = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(discovery)


class Document(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.tags = []
        self.title = ""
        self.in_title = False
        self.schema = []
        self.in_schema = False
        self.feed(path.read_text())

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        self.in_title |= tag == "title"
        self.in_schema |= tag == "script" and attrs.get("type") == "application/ld+json"

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "script":
            self.in_schema = False

    def handle_data(self, value):
        if self.in_title:
            self.title += value
        if self.in_schema:
            self.schema.append(json.loads(value))

    def elements(self, tag, **attrs):
        return [
            values
            for name, values in self.tags
            if name == tag and all(values.get(k) == v for k, v in attrs.items())
        ]

    def meta(self, name):
        values = self.elements("meta", name=name)
        assert len(values) == 1, (name, values)
        return values[0]["content"]


def build(destination, **environment):
    env = {
        k: v for k, v in os.environ.items() if k not in {"CF_PAGES", "DOCS_ENV", "DOCS_SITE_URL"}
    }
    env.update(DOCS_ENV="production", DOCS_SITE_URL=BASE)
    env.update(environment)
    result = subprocess.run(
        [sys.executable, "-m", "mkdocs", "build", "--strict", "--site-dir", str(destination)],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return destination


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    return build(tmp_path_factory.mktemp("docs-production"))


def sitemap_urls(site):
    root = ElementTree.parse(site / "sitemap.xml")
    return [el.text for el in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]


def test_installer_is_published_without_modification(site):
    assert (site / "install-studio.sh").read_bytes() == (
        ROOT / "scripts/install-studio.sh"
    ).read_bytes()


def test_brand_assets_resolve_from_nested_pages_and_readmes(site):
    assets = ROOT / "docs/assets/brand"
    for source in assets.glob("*.svg"):
        assert (site / "_static/brand" / source.name).read_bytes() == source.read_bytes()
        svg = ElementTree.parse(source).getroot()
        assert svg.attrib.get("viewBox")
        assert all(
            node.tag.rsplit("}", 1)[-1] not in {"text", "script", "image"} for node in svg.iter()
        )
    for relative in ["index.html", "studio/index.html", "reference/indicators/ema/index.html"]:
        page = Document(site / relative)
        base = BASE + relative.removesuffix("index.html")
        home = page.elements("a", **{"aria-label": "OpenBacktesting home"})
        assert (
            len(home) == 1
            and target_path(site, urljoin(base, home[0]["href"])) == site / "index.html"
        )
        icons = page.elements("link", rel="icon")
        assert len(icons) == 1
        assert (
            target_path(site, urljoin(base, icons[0]["href"])).read_bytes()
            == (assets / "favicon.svg").read_bytes()
        )
        brand = [img for img in page.elements("img") if "_static/brand/" in img.get("src", "")]
        assert len(brand) == 5
        for img in brand:
            assert img["alt"] == "" and target_path(site, urljoin(base, img["src"])).is_file()
    for readme in [
        ROOT / "README.md",
        ROOT / "studio/README.md",
        *sorted((ROOT / "docs/readme").glob("README.*.md")),
    ]:
        parsed = Document(readme)
        wordmark = parsed.elements("img", alt="OpenBacktesting")
        assert len(wordmark) == 1
        assert (readme.parent / wordmark[0]["src"]).resolve() == assets / "wordmark.svg"
        dark = parsed.elements("source", media="(prefers-color-scheme: dark)")
        assert len(dark) == 1
        assert (readme.parent / dark[0]["srcset"]).resolve() == assets / "wordmark-white.svg"


def target_path(site, url, base=BASE):
    parts = urlsplit(url)
    assert parts.netloc == urlsplit(base).netloc
    assert parts.path.startswith(urlsplit(base).path)
    relative = unquote(parts.path.removeprefix(urlsplit(base).path))
    target = site / relative
    assert target.resolve().is_relative_to(site.resolve())
    return target / "index.html" if target.is_dir() else target


def test_every_page_has_portable_markdown_and_search_metadata(site):
    indexed, titles, descriptions = [], [], []
    documents = list(site.rglob("*.html"))
    assert len(documents) > 300
    for path in documents:
        doc = Document(path)
        if path.name == "404.html":
            assert "noindex" in doc.meta("robots")
            continue
        canonical = doc.elements("link", rel="canonical")
        assert len(canonical) == 1
        url = canonical[0]["href"]
        assert target_path(site, url) == path
        markdown = doc.elements("link", rel="alternate", type="text/markdown")
        assert len(markdown) == 1
        raw_url = urljoin(url, markdown[0]["href"])
        raw = target_path(site, raw_url)
        assert raw.is_file() and raw.read_text().startswith("# ")
        buttons = [a for a in doc.elements("button") if "data-copy-markdown" in a]
        assert len(buttons) == 1 and buttons[0]["data-markdown-url"] == markdown[0]["href"]
        assert len(doc.elements("h1")) == 1
        for tag, attrs in doc.tags:
            for attribute in ("href", "src"):
                link = attrs.get(attribute)
                if not link:
                    continue
                destination = urljoin(url, link)
                if destination.startswith(BASE):
                    assert target_path(site, destination).is_file(), (path, destination)
        assert doc.meta("description")
        assert doc.elements("meta", property="og:url")[0]["content"] == url
        assert urljoin(url, doc.elements("link", rel="describedby")[0]["href"]) == BASE + "llms.txt"
        if "noindex" in doc.meta("robots"):
            assert "/repository/" in url
            continue
        indexed.append(url)
        titles.append(doc.title)
        descriptions.append(doc.meta("description"))
        assert len(doc.schema) == 1
        graph = doc.schema[0]["@graph"]
        article = next(item for item in graph if item["@type"] == "TechArticle")
        assert article["url"] == url and article["description"] == doc.meta("description")
        assert "dateModified" not in article and "aggregateRating" not in article
        if url != BASE:
            trail = next(item for item in graph if item["@type"] == "BreadcrumbList")
            assert trail["itemListElement"][-1]["item"] == url
            for crumb in trail["itemListElement"]:
                assert target_path(site, crumb["item"]).is_file()
    assert len(indexed) == len(list((ROOT / "docs/core").rglob("*.md")))
    assert len(titles) == len(set(titles)), Counter(titles)
    assert len(descriptions) == len(set(descriptions)), Counter(descriptions)
    assert set(sitemap_urls(site)) == set(indexed)
    assert len(sitemap_urls(site)) == len(indexed)
    assert b"<lastmod>" not in (site / "sitemap.xml").read_bytes()
    assert (
        gzip.decompress((site / "sitemap.xml.gz").read_bytes())
        == (site / "sitemap.xml").read_bytes()
    )


def test_llm_indexes_and_all_markdown_links_resolve(site):
    index = (site / "llms.txt").read_text()
    assert index == (site / "llm.txt").read_text()
    assert len(index) < 20000 and index.startswith("# OpenBacktesting\n\n>")
    assert "## Start here" in index and "## Optional" in index
    assert "/reference/indicators/index.md" in index
    full = (site / "llms-full.txt").read_text()
    for path in [*site.rglob("*.md"), site / "llms.txt"]:
        content = discovery.FENCE.sub("", path.read_text())
        for match in discovery.LINK.finditer(content):
            url = match["url"]
            if url.startswith(BASE):
                assert target_path(site, url).is_file(), (path, url)
            else:
                assert urlsplit(url).scheme or url.startswith(("//", "#")), (path, url)
    # Source examples, tables, and validity warnings are carried into LLM exports.
    for source in (ROOT / "docs/core").rglob("*.md"):
        rel = source.relative_to(ROOT / "docs/core")
        raw = site / rel.parent / ("index.md" if rel.name == "index.md" else rel.stem + "/index.md")
        text = raw.read_text()
        assert discovery.FENCE.findall(text) == discovery.FENCE.findall(source.read_text())
        source_blocks = [m[0] for m in discovery.FENCE.finditer(source.read_text())]
        assert source_blocks == [m[0] for m in discovery.FENCE.finditer(text)]
        assert text in full
    assert "ready` is diagnostic" in full
    assert "Sitemap: " + BASE + "sitemap.xml" in (site / "robots.txt").read_text()
    headers = (site / "_headers").read_text()
    assert "Content-Type: text/markdown; charset=utf-8" in headers
    assert "https://:project.pages.dev/*\n  X-Robots-Tag: noindex" in headers


def test_preview_cannot_be_indexed_and_base_paths_work(tmp_path):
    base = "https://docs.example.test/manual/"
    site = build(tmp_path / "preview", CF_PAGES="1", DOCS_ENV="preview", DOCS_SITE_URL=base)
    assert not sitemap_urls(site)
    assert "Sitemap:" not in (site / "robots.txt").read_text()
    assert "/*\n  X-Robots-Tag: noindex" in (site / "_headers").read_text()
    for path in site.rglob("*.html"):
        doc = Document(path)
        assert "noindex" in doc.meta("robots")
    page = Document(site / "reference/indicators/ema/index.html")
    canonical = page.elements("link", rel="canonical")[0]["href"]
    assert canonical == base + "reference/indicators/ema/"
    raw = page.elements("link", rel="alternate")[0]["href"]
    assert target_path(site, urljoin(canonical, raw), base).is_file()
    for match in discovery.LINK.finditer((site / "llms.txt").read_text()):
        assert target_path(site, match["url"], base).is_file()


def test_metadata_is_extracted_from_visible_prose():
    parser = discovery.PageText()
    parser.feed(
        '<h1>EMA <code>ta.ema</code><a class="headerlink">¶</a></h1><pre><code>ignored</code></pre><p>Read <a href="x">this guide</a> for examples.</p>'
    )
    assert "".join(parser.heading) == "EMA ta.ema"
    assert parser.paragraphs == ["Read this guide for examples."]
    parser = discovery.PageText()
    parser.feed(
        '<p><a href="index.md">Indicator catalog</a> · <a href="guide.md">How to use indicators</a></p><p>Smooth prices.</p>'
    )
    assert parser.paragraphs == ["Smooth prices."]


@pytest.mark.parametrize(
    "cloudflare,environment,indexable",
    [("", "", True), ("", "preview", False), ("1", "", False), ("1", "production", True)],
)
def test_indexing_environment_policy(monkeypatch, cloudflare, environment, indexable):
    monkeypatch.setenv("CF_PAGES", cloudflare)
    monkeypatch.setenv("DOCS_ENV", environment)
    config = SimpleNamespace(site_url=BASE, extra={})
    discovery.on_config(config)
    assert config.extra["docs_indexable"] is indexable
