# Security policy

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/lucidcog/openbacktesting/security/advisories/new) to contact repository maintainers. Do not disclose suspected vulnerabilities, credentials, or exploit details in public issues or discussions.

Include the affected version or commit, component, operating system, reproduction steps, expected security boundary, and potential impact. Use a minimal proof of concept with synthetic data, and remove secrets and personal information. Coordinate disclosure through the private advisory before publishing details.

## Versions and fixes

Report issues against any version, and indicate whether they reproduce on the current `main` branch. Fixes are developed on `main`; there is no separate long-term support or guaranteed backport policy. Response and remediation times are not guaranteed.

## Execution boundaries

OpenBacktesting and Studio execute user-supplied Python strategy code. They are not code sandboxes. Run only trusted strategies and load only trusted serialized Python objects. Studio is a local workspace; do not expose its server or session credentials to untrusted networks or users.

Suspected bypasses of Studio's authentication, origin checks, or workspace filesystem boundaries should be reported privately. Ordinary calculation errors and reproducible execution bugs belong in the public issue tracker unless they cross a security boundary.
