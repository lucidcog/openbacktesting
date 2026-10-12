# Input declarations and configuration

## User script: declare an Input

Strategies can declare configurable parameters as class fields. `title` is required and must be unique within the strategy, including across groups and inherited fields. It serves as both display name and configuration key, without an additional `id`. Field names provide access in Python code only.

```python
from openbacktesting import Strategy, backtest, inputs


@backtest(commission_value=0.2, exclusive_orders=True)
class ConfigurableSma(Strategy):
    length = inputs.int(20, minval=1, title="Moving-average period", group="Moving averages")

    def init(self):
        self.line = self.ta.sma(length=self.length)

    def next(self):
        pass

```

Users need not write schema, request, `inputs.describe()`, `bt.run()`, or `bt.run_inputs()`. See the [complete Input example](../../../examples/strategies/all_inputs.py) for declarations and actual reads of all nine input types, and the [built-in EMA input example](../../../examples/strategies/ema_inputs.py) for a configurable dual-EMA strategy. Both define only the strategy and default backtest settings; `self.length` reads this run's resolved value inside the strategy.

| Declaration | Runtime value and configuration representation | Constraints |
| ----------- | ---------------------------------------------- | ----------- |
| `inputs.bool` | bool | Rejects numeric and string coercion |
| `inputs.int` | int | Supports options or minval/maxval/step; rejects bool and floats |
| `inputs.float` | float | Same controls; finite integers convert losslessly; rejects NaN/Infinity |
| `inputs.price` | float | Retains the price kind; permits negatives; rejects numeric bounds/options |
| `inputs.string` | str | Supports options and preserves original whitespace |
| `inputs.time` | Unix milliseconds as an integer | Does not guess units; int/time range is `±(2^53−1)` |
| `inputs.session` | Normalized session string | Supports overnight periods, multiple intervals, weekday suffixes, and 24x7; does not filter market data automatically |
| `inputs.color` | Runtime `Color`; configuration `#RRGGBBAA` | Defaults/native overrides accept Color or six/eight-digit strings; normalized to uppercase eight-digit encoding |
| `inputs.enum` | Python Enum member; configuration stores the member name | Default member determines enum type; supports options; rejects aliases and members of other types |

Color Inputs now consistently return `Color`: both `inputs.color("#22aa44", title="Up color")` and `inputs.color(colors.TEAL, title="Up color")` are valid declarations; import `colors` from the package root first. Inside strategies, derive colors directly with `self.up_color.with_transparency(85)` and pass them to plotting without conversion; the Input itself remains read-only. Call `to_hex()` explicitly when text is needed, rather than slicing or comparing the runtime value as a string.

`bt.run(up_color=...)` accepts Color or strings; title-based `run_inputs` requests accept only strings, rejecting Color, None, and object mappings. Discovery, input snapshots, and schemaHash still use normalized strings; equivalent six-digit/eight-digit/Color defaults produce identical digests. grid candidates are normalized to Color before being passed to constraint and native heatmap labels; configuration and result snapshots remain strings.

See [plotting and colors](plotting.md) and the [color API](../reference/colors.md) for complete usage. The current core supports input declarations and injection without a desktop color picker.

For example, `inputs.enum(Mode.FAST, title="Mode", options=[Mode.FAST, Mode.SLOW])` stores `"FAST"` or `"SLOW"` in configuration, while the native Python runtime value remains a `Mode` member. The enum type identifier is exported automatically from the class; use importable module-level strategy and enum classes across processes. Numeric options are mutually exclusive with bounds/step; step describes the adjustment increment, not divisibility. Session `24x7` normalizes to `0000-0000:1234567`; omitting weekdays means every day. Consumers interpret timezone and trading calendar separately.

Public presentation hints support `tooltip/group/inline/display/active/confirm`. active may be a boolean constant or `{"title": "A boolean input"}`; references must be valid and acyclic. Disabling an input, hiding it with display, or supplying confirm does not remove fields, skip validation, or launch a UI. Input fields are read-only during execution; use ordinary local variables or other instance fields for derived computations.

The low-level runtime API serves frameworks and native Python callers: `bt.run_inputs(request)` matches by title, while `bt.run(length=30)` matches by field name, using the same validation rules. Declared strategies reject undeclared attributes. Validation failure constructs neither strategy nor broker and does not silently fall back to defaults. `inputs.InputError` exposes `code/title/expected/actual_type`; the title-based entry point accepts mapping objects, and callers must reject duplicate keys when decoding JSON text.

Result `attrs["input_snapshot"]` contains the format version, declaration digest, core version, all effective values, and explicitly overridden titles; the statistics index is unchanged. Changing only titles, fields, or descriptions also changes the declaration digest, requiring rediscovery and confirmation for old requests. Renamed titles must not be automatically migrated by old field names. This snapshot is not a complete project snapshot of code, data, or dependencies.

Declared strategies support `grid` optimization with candidates passed by Python field name. All candidates are validated before constraint, sampling, or dispatch. The initial release explicitly rejects `sambo/skopt` for declared strategies; legacy strategies without input declarations retain their parameter and optimization behavior. The fractional-backtest title entry point still performs native-unit conversion.
