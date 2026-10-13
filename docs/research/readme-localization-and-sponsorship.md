# README localization and sponsorship research

## Conclusion

Keep the root `README.md` as the canonical English entry point, and add a small language switcher near the top of each localized README. For the first localization set, use English, Spanish, Brazilian Portuguese, French, German, Italian, and Hindi. This is a scope recommendation based on the requested Europe, Americas, and India audience; it is not a claim about readership or language demographics. Keep the localized files focused on the overview, installation, quick start, support, contribution, license, and sponsor links, and link to the fuller manual until there is a maintained translation of that manual.

## README requirements from GitHub

GitHub's [official README guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes) says that a README should explain why the project is useful, what users can do with it, and how they can use it. GitHub's typical README content is:

- what the project does;
- why it is useful;
- how users get started;
- where users can get help; and
- who maintains and contributes to it.

The same guidance recommends relative links and image paths for repository content because they continue to work in clones and across branches. GitHub generates a table of contents from headings, so the README can use normal headings rather than maintaining a separate hand-written TOC. GitHub truncates rendered README content beyond 500 KiB and recommends putting longer material in a wiki or linked documentation.

GitHub's [open-source contribution guidance](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-open-source) describes the README as the place where users and contributors quickly understand the project and find links to additional documentation. It also identifies contribution, code-of-conduct, license, and security guidance as separate repository expectations. The README should link to those files when they exist instead of duplicating their policies.

### Actionable outline for this repository

1. Project title, one-sentence value statement, status/version badges, and language links.
2. What the package does, its useful boundaries, and the current limitations.
3. Supported Python versions and installation commands.
4. A minimal runnable backtest and links to the quickstart/manual.
5. Feature and documentation map, with details kept in `docs/`.
6. Development, test, and artifact verification commands.
7. Help, issue reporting, contributing, and security links where available.
8. License and third-party/source-attribution caveats.
9. A clearly labeled sponsor disclosure with the Pineify logo and link.

## Pineify asset verification

The [Pineify homepage](https://pineify.app/en) identifies the product and links to its public tools and documentation. The [Pineify Manual](https://pineify.app/manual/) exposes official brand assets, including `brand-light.svg`, `brand-dark.svg`, `brand_800_800.png`, and `pineify-logo-2.svg`.

The selected source asset is [pineify-logo-2.svg](https://pineify.app/manual/pineify-logo-2.svg). On 2026-10-13 it returned HTTP 200 with `image/svg+xml`; it is a 180x180 transparent vector mark. The repository copy at [`docs/assets/pineify-logo.svg`](../assets/pineify-logo.svg) is byte-for-byte identical to that URL and has SHA-256 `0f559ddface01642a2505e7c59e8cb3cd8cf25120b2498b459e0788aa0d11084`. It was not recolored, cropped, or otherwise reconstructed, so it is suitable for a relative image path in the README and remains legible on light and dark backgrounds.

Suggested README embedding:

```markdown
[![Pineify](docs/assets/pineify-logo.svg)](https://pineify.app/en)

Pineify is the project's top paid sponsor.
```

Keep the sponsor wording explicit as authorized by the project owner. Do not imply a product integration, endorsement, or partnership beyond the paid sponsorship statement. Asset provenance and the unchanged-file checksum are recorded in [`docs/assets/pineify-logo-attribution.md`](../assets/pineify-logo-attribution.md).

## Limits and maintenance

The official Pineify pages expose the asset URLs but do not state separate logo-license terms in the retrieved page content. Preserve the exact source artwork and attribution record; this report does not make a legal determination. If a future README needs a full wordmark or a dark-mode-specific variant, use the official `brand-light.svg` and `brand-dark.svg` files from the same manual rather than rebuilding the mark.
