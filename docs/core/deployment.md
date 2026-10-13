# Deploy the documentation to Cloudflare Pages

The documentation builds to a static site with navigation, page outlines, and browser-side full-text search. No application server or search service is required.

## Build command

From the repository root, using Python 3.12–3.14:

```sh
bash scripts/build_docs.sh
```

The script installs a pinned uv version in `build/docs-tools/`, installs only the locked `docs` dependency group in `build/docs-env/`, and runs `mkdocs build --strict`. It leaves the project's development environment untouched. The deployable output is **`build/docs/`**, including all HTML and Markdown pages, static assets, `404.html`, the search index, LLM indexes, sitemap, robots file, and Cloudflare response headers. Deploy only that directory.

The build renders the committed Markdown. After changing API source or documentation templates, regenerate references and commit the resulting Markdown before deployment; see [documentation maintenance](development.md#documentation-and-generated-interfaces).

## Cloudflare Pages settings

Connect the repository to a Pages project using Git integration, then enter:

| Setting | Value |
| --- | --- |
| Framework preset | `None` |
| Root directory | Repository root; leave blank |
| Build command | `bash scripts/build_docs.sh` |
| Build output directory | `build/docs` |
| Build environment variable | `PYTHON_VERSION=3.13.3` |
| Build environment variable | `SKIP_DEPENDENCY_INSTALL=1` |
| Production environment variable | `DOCS_ENV=production` |
| Preview environment variable | `DOCS_ENV=preview` |

Apply the Python and dependency settings to both environments; scope `DOCS_ENV` separately as shown. The script handles dependency installation, so automatic installation is disabled. Cloudflare builds without an explicit production environment default to `noindex`. These settings follow Cloudflare's [custom static-site build configuration](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/) and [build image configuration](https://developers.cloudflare.com/pages/configuration/build-image/).

Choose the branch you want to publish as the production branch. Commit and push the site configuration, scripts, `pyproject.toml`, `uv.lock`, documentation, and referenced examples before triggering the first build. Pages can also produce preview deployments for review branches and pull requests.

The canonical production address is **`https://docs.openbacktesting.com/`**, configured in `mkdocs.yml`. Attach that custom domain to the Pages project. To move the site, override `DOCS_SITE_URL` with the new HTTPS root, including any path prefix, and rebuild. Internal navigation remains relative; canonical URLs, structured data, sitemap, and exported Markdown links share the configured root. No SPA catch-all redirect is needed: every documentation route has its own HTML page, and missing routes use the generated `404.html`.

## Analytics

The shared theme loads `https://umami.pineify.app/script.js` once per page with website ID `038fca77-0084-4fd6-a285-f3c22c7da604`. Umami records pageviews automatically and the following explicit click events:

| Event | Action | Properties |
| --- | --- | --- |
| `docs-sponsor-click` | Open Pineify | `placement`: `header` or `footer` |
| `docs-github-click` | Open the GitHub repository | `placement`: `header` |
| `docs-quickstart-click` | Open the first backtest from the home page | `placement`: `home-primary` or `home-tutorials` |
| `docs-examples-click` | Open runnable examples from the home page | `placement`: `home-tutorials` |
| `docs-markdown-copy` | Click Copy as Markdown | None |
| `docs-markdown-view` | Open View Markdown | None |
| `docs-code-copy` | Click a code block's copy button | None |
| `docs-company-click` | Open LucidCog | `placement`: `footer` |
| `docs-llm-index-click` | Open the LLM index | `placement`: `footer` |

Copy events measure clicks, not successful clipboard writes. Umami includes the current page URL and hostname; no clipboard contents, code, or search terms are added as event properties. Template and Markdown links use `data-umami-event` attributes; `_static/analytics.js` handles Material's dynamically created code-copy buttons.

The same website ID can collect traffic from multiple subdomains. The dashboard's Domain field filters self-referrals; it is not a collection allowlist. This script has no `data-domains` restriction, so local and preview visits also report unless tracking is disabled. To restrict collection, list each allowed hostname explicitly with `data-domains`; a root domain does not automatically allow its subdomains. See Umami's [website settings](https://docs.umami.is/docs/add-a-website) and [tracker configuration](https://docs.umami.is/docs/tracker-configuration).

For local checks, block `/api/send` or set `localStorage.setItem("umami.disabled", "1")` before loading the page. After deployment, verify a pageview and the relevant events in Umami, using the hostname filter to isolate `docs.openbacktesting.com`.

## Markdown and LLM access

Every page has **Copy as Markdown** and **View Markdown** below its heading. Copying uses the authored Markdown, preserving fenced code and tables, with absolute links that work outside the browser. When clipboard access is unavailable, the page displays selectable Markdown for manual copying. Viewing Markdown works without JavaScript.

The build generates:

| Resource | Purpose |
| --- | --- |
| `/<page>/index.md` | Markdown counterpart of each directory-style HTML page; the home page uses `/index.md` |
| `/llms.txt` | Concise, grouped discovery index with links to tutorials, guides, references, and the indicator catalog |
| `/llm.txt` | Compatibility alias containing the same index |
| `/llms-full.txt` | Combined manual and runnable example sources for larger contexts |
| `/sitemap.xml` and `/sitemap.xml.gz` | Canonical, indexable HTML pages |
| `/robots.txt` | Allows crawling and advertises the production sitemap |

HTML exposes `rel="alternate" type="text/markdown"` and `rel="describedby"` links following the [llms.txt proposal](https://llmstxt.org/). LLM exports are generated from the same content as the site; edit the underlying documentation, not build output.

## Search visibility

Pages have descriptive titles, individual summaries, canonical URLs, visible breadcrumbs, matching `TechArticle` and `BreadcrumbList` structured data, and Open Graph metadata. Content and navigation render as static HTML. Sponsor placements and page tools are excluded from search snippets. Bundled repository copies remain accessible but use `noindex` to avoid competing with the manual. The sitemap omits duplicates, raw exports, 404 pages, and preview pages. It does not invent modification dates or ratings.

The generated `_headers` uses [Cloudflare Pages header rules](https://developers.cloudflare.com/pages/configuration/headers/) to serve UTF-8 Markdown, keep raw exports out of search results, and prevent `pages.dev` copies from being indexed. Preview builds additionally use `noindex` in both HTML and HTTP headers. Crawling remains allowed so crawlers can read these directives. When hosting elsewhere, configure the equivalent response headers on that host; MkDocs' local server does not apply `_headers`.

Google's [SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide) recommends useful, accurate content, descriptive titles, discoverable links, and good page experience. Its [AI features guidance](https://developers.google.com/search/docs/appearance/ai-features) applies the same requirements to AI Overviews and AI Mode: pages must be indexed and eligible for snippets. LLM files and structured data do not guarantee rankings, indexing, or AI citations.

After publishing:

1. Verify the custom domain, HTTPS, successful HTML/Markdown responses, and real 404 responses. Confirm production HTML has no `noindex` header or meta tag and previews do.
2. Confirm CDN and bot-management settings allow intended search crawlers and do not challenge public documentation requests.
3. Verify domain ownership in Search Console, submit `https://docs.openbacktesting.com/sitemap.xml`, and inspect the home page, quickstart, and an indicator URL. Confirm Google's selected canonical agrees with the published canonical.
4. Use Rich Results Test and PageSpeed Insights on the deployed domain. Monitor Search Console indexing, queries, clicks, and Core Web Vitals; address observed problems and update examples when APIs change.

These checks require a live deployment and access to the domain's Search Console property. Local builds validate generated artifacts, not Google's indexing or field performance.

## Review locally

```sh
uv run --locked --group docs mkdocs serve
```

Open `http://127.0.0.1:8000`. Use the sidebar for topics and indicator categories, the right-hand outline for sections, and the search field for names such as `OrderRequest`, `ta.ema`, or `commission`. On small screens, navigation and search open from the header buttons.
