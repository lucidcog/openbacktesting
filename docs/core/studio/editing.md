---
title: Studio — edit code and parameters
description: Save Python strategy files, change inputs, and reuse presets and data profiles.
---

# Edit code and parameters

Open **Code**, edit, and use **Save strategy** or **Ctrl/Cmd+S** while the editor is focused. Saving writes to the actual local Python file. If the file changed elsewhere, resolve the conflict before saving; failed saves retain your draft. An opened historical source snapshot is read-only.

Open **Strategy settings** to change **Inputs** without editing the Python declarations. **Apply to next run** updates the next configuration; it does not start a backtest. Click **Run** when ready. If code has unsaved changes, **Save & Run** saves before preparing the new run. A new or changed input schema may require review again.

**Save preset** stores reusable inputs and properties as JSON; **Save profile** stores a data configuration. Neither rewrites the strategy's default values. Every submitted run keeps an immutable configuration, so later edits do not change its result.
