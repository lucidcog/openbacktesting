---
title: Studio — troubleshooting
description: Resolve installation, strategy discovery, data, workspace, and missing-result issues.
---

# Troubleshooting

Use these checks when installation, strategy discovery, or saved results do not behave as expected. See [Install and launch](installation.md) for setup commands and [Inspect logs](logs.md) for run diagnostics.

| Symptom | What to check |
| --- | --- |
| `openbacktesting-studio` is not found | Use the application shortcut or `~/.local/share/openbacktesting-studio/studio`; the command alias needs `~/.local/bin` on your PATH. |
| Installation fails | Check the reported step and network connection, then repeat the installation command. An existing installation remains available. |
| No compatible strategy is discovered | The saved module must expose one `@backtest` strategy; install its imports into the selected interpreter. |
| A run fails or data is rejected | Open **Logs** and inspect the source location; check column mappings, time encoding, timezone, and ordered unique bars. |
| Directory switching is disabled | Save unsaved code and finish or cancel the active run or optimization. |
| An old result has no chart or source | Those resources were not included. Read the report, or explicitly run locally trusted source to create a new complete result. |
| The remembered directory disappears | Use the same browser profile and origin, including the port, and check that the directory still exists. |
