# Maintaining README translations

[English README](../../README.md) is the source of truth. Translations are intentional localized copy under the repository's English-default policy. The manual and code remain in English.

## Supported languages

| Language | File |
| --- | --- |
| English | [README.md](../../README.md) |
| Simplified Chinese | [README.zh-CN.md](README.zh-CN.md) |
| Spanish | [README.es.md](README.es.md) |
| Brazilian Portuguese | [README.pt-BR.md](README.pt-BR.md) |
| French | [README.fr.md](README.fr.md) |
| German | [README.de.md](README.de.md) |
| Italian | [README.it.md](README.it.md) |
| Hindi | [README.hi.md](README.hi.md) |

This initial set follows the project's focus on Europe, the Americas, and India. It is a practical starting point, not a claim to cover every language in those regions; English remains available to all readers. Simplified Chinese is also provided at the project owner's request. Keep English first and Simplified Chinese second in every language switcher. Further languages can be added through a pull request.

## Update rules

1. Update the English README and every affected translation in the same change. Preserve section order and factual coverage, including sponsor disclosure, limitations, and license/provenance notices.
2. Translate prose and link labels naturally. Keep commands, code blocks, package names, API identifiers, result keys, versions, and URLs unchanged. Do not imply that the detailed manual is translated.
3. Resolve links relative to each file. From this directory, use `../../` for repository-root files, `../core/` for the manual, and `../assets/` for sponsor images. Check fragment identifiers against the destination headings.
4. Retain Pineify's official, unmodified logo and linked top paid sponsor placement in every language. Keep asset provenance in [the asset notes](../assets/pineify-logo-attribution.md).
5. Run `uv run --locked python scripts/check_package.py`, compare executable snippets against English, and execute changed examples. Review rendered Markdown, language navigation, local links, and logo display before submitting.

Avoid adding unsupported installation methods, benchmark claims, compatibility guarantees, or sponsor product claims during translation. Corrections to underlying facts belong in English and all translations together.
