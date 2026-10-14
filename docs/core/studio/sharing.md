---
title: Studio — save, share, and reopen
description: Keep workspace history, export and import result archives, and open read-only reports.
---

# Save, share, and reopen

Studio stores history, snapshots, profiles, and experiments under `.openbacktesting/studio/` inside the chosen directory. Keep that directory to retain your history; consider ignoring it in your strategy repository.

**Export result** creates an `.obstudio` archive. Reports, chart data, and provenance are included by default; source, normalized raw data, and logs are opt-in. Review the contents before sharing. Use **Import result** in Studio, or launch a read-only viewer:

```sh
openbacktesting-studio view /path/to/result.obstudio --no-open
openbacktesting-studio view /path/to/portfolio.json --no-open
```

A standalone Portfolio JSON provides reports; it does not imply that chart data is present. Imported results do not execute embedded Python.

