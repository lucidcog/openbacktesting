"""Connect the existing Markdown manual and local examples to MkDocs."""

from __future__ import annotations

import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

from mkdocs.structure.files import File, InclusionLevel

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/core"
LINK = re.compile(r"(?P<prefix>!?\[[^\]\n]*\]\()(?P<url>[^\s)]+)(?P<suffix>\))")
FENCE = re.compile(r"^(`{3,}|~{3,}).*?^\1[ \t]*$", re.MULTILINE | re.DOTALL)


def site_path(path):
    """Preserve manual URLs and bundle linked repository files under one prefix."""
    if path.is_relative_to(DOCS):
        return path.relative_to(DOCS).as_posix()
    uri = "repository/" + path.relative_to(ROOT).as_posix()
    return uri + ".md" if path.suffix == ".py" else uri


def local_target(url, source):
    parts = urlsplit(url)
    if parts.scheme or parts.netloc or not parts.path:
        return None
    path = (source.parent / unquote(parts.path)).resolve()
    return path if path.is_relative_to(ROOT) and path.is_file() else None


def on_config(config):
    """Build category navigation from the same index as the indicator catalog."""
    rows = json.loads((DOCS / "_static/indicator-index.json").read_text())
    groups = {}
    for row in rows:
        category = row["category"] if row["status"] == "Available" else "Unavailable entries"
        label = row["id"].removeprefix("ta.")
        groups.setdefault(category, []).append({label: "reference/indicators/" + row["href"]})
    for section in config.nav:
        if "Indicators" in section:
            section["Indicators"] = [
                {"Catalog": "reference/indicators/index.md"},
                *({name: groups[name]} for name in sorted(groups)),
            ]
    return config


def on_files(files, config):
    """Include only repository files linked by the manual, without copying sources."""
    files.append(
        File.generated(
            config,
            "install-studio.sh",
            abs_src_path=str(ROOT / "scripts/install-studio.sh"),
        )
    )
    files.append(
        File.generated(
            config,
            "_static/pineify-logo.svg",
            abs_src_path=str(ROOT / "docs/assets/pineify-logo.svg"),
        )
    )
    pending = [Path(file.abs_src_path) for file in files.documentation_pages()]
    visited = set()
    while pending:
        source = pending.pop()
        if source in visited:
            continue
        visited.add(source)
        for match in LINK.finditer(FENCE.sub("", source.read_text())):
            target = local_target(match["url"], source)
            if target is None or target.is_relative_to(DOCS):
                continue
            uri = site_path(target)
            if files.get_file_from_path(uri) is not None:
                continue
            if target.suffix == ".py":
                relative = target.relative_to(ROOT).as_posix()
                content = (
                    f"# {target.name}\n\nSource: `{relative}`\n\n"
                    f"````python\n{target.read_text()}\n````\n"
                )
                file = File.generated(config, uri, content=content)
            else:
                file = File.generated(config, uri, abs_src_path=str(target))
            file.inclusion = InclusionLevel.NOT_IN_NAV
            files.append(file)
            if target.suffix == ".md":
                pending.append(target)
    return files


def on_page_markdown(markdown, page, config, files):
    """Rewrite repository links for the site while leaving authored Markdown intact."""
    uri = page.file.src_uri
    if uri.startswith("repository/") and uri.endswith(".py.md"):
        return markdown
    source = ROOT / uri.removeprefix("repository/") if uri.startswith("repository/") else DOCS / uri

    def rewrite(match):
        target = local_target(match["url"], source)
        if target is None:
            return match[0]
        parts = urlsplit(match["url"])
        relative = posixpath.relpath(site_path(target), posixpath.dirname(uri) or ".")
        url = urlunsplit(("", "", relative, parts.query, parts.fragment))
        return match["prefix"] + url + match["suffix"]

    # Code examples must remain byte-for-byte identical to their Markdown source.
    output, start = [], 0
    for fence in FENCE.finditer(markdown):
        output.extend([LINK.sub(rewrite, markdown[start : fence.start()]), fence[0]])
        start = fence.end()
    output.append(LINK.sub(rewrite, markdown[start:]))
    return "".join(output)
