# Add strategy visuals

The framework collects plotting declarations and exports their data. It does not include a chart renderer. The [complete plotting example](../reference/plotting.md#declare-and-export-visuals) adds an EMA, an RSI pane, a level, and candle colors.

## Choose a phase

- In `init()`, create panes and static lines/histograms/levels/fills using registered single-channel handles.
- In `next()`, place event markers and apply current-bar background/candle colors.
- After `run()`, call `openbacktesting.plotting.export_result(result)` to obtain a plain dictionary for your renderer or JSON file.

References belong to one run. A line needs an indicator/data handle, a fill needs two compatible plot references, and a marker at `position="price"` needs a price. See [all plotting parameters](../reference/plotting.md).

## Color values and strings

Import `Color` or `colors` from `openbacktesting`. `Color.rgb(30, 120, 220)` creates a color; `.with_transparency(80)` makes it 80% transparent. Six/eight-digit hex strings are also accepted. Color inputs produce Color values; call `.to_hex()` when you need text.

`self.plotting.bar_color(color)` colors the current candle, and `bg_color(color, pane=...)` colors the current background. `None` clears an override. The last write for a bar/target wins, and a new bar does not inherit the previous color automatically.

[Color and gradients](../reference/colors.md) · [Plotting limits and exports](../reference/plotting.md#colors-and-limits)
