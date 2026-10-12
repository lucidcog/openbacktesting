"""All nine Input types: declarations, enum choices, colors, times, and sessions at runtime.

The first 120 bundled GOOG daily bars, with no extra dependencies; plot and log only, without orders, positions, or fees.
The host executes author scripts; see the example index for commands. title is the configuration key, while field names support self access.
time uses Unix milliseconds and controls the start of coloring here; session only validates and normalizes strings,
This example logs its value without filtering daily data or providing trading calendars or intraday session checks.
group/inline/display/active/confirm are UI hint metadata; they do not start or control a UI themselves.
"""

from enum import Enum

from openbacktesting import Strategy, backtest, inputs


class AverageKind(Enum):
    # Configuration stores member names "EMA" / "SMA", not their .value here.
    EMA = "Exponential moving average"
    SMA = "Simple moving average"


@backtest()
class AllInputs(Strategy):
    highlight = inputs.bool(True, title="Show highlights", group="Display")
    length = inputs.int(20, title="Moving-average period", minval=2, maxval=100, step=1, group="Moving average")
    multiplier = inputs.float(
        1.02,
        title="Highlight multiplier",
        minval=1.0,
        maxval=2.0,
        step=0.01,
        group="Display",
        active={"title": "Show highlights"},
        tooltip="Color when close exceeds the moving average times this multiplier; step is an adjustment increment, not a divisibility constraint.",
    )
    source = inputs.string(
        "close", title="Price source", options=["close", "hl2"], group="Moving average", inline="Selection"
    )
    average_kind = inputs.enum(
        AverageKind.EMA,
        title="Moving-average type",
        options=[AverageKind.EMA, AverageKind.SMA],
        group="Moving average",
        inline="Selection",
    )
    reference_price = inputs.price(
        100.0,
        title="Reference price",
        group="Display",
        confirm=True,
        tooltip="Draw a horizontal line only; price does not support minval/maxval/step/options.",
    )
    start_time = inputs.time(
        1092873600000,
        title="Highlight start",
        group="Display",
        tooltip="2004-08-19 00:00:00 UTC, in milliseconds.",
    )
    session = inputs.session(
        "24x7",
        title="Session description",
        display="data_window",
        tooltip="Show the normalized value only, without filtering data; 24x7 becomes 0000-0000:1234567.",
    )
    line_color = inputs.color("#22aa44", title="Moving-average color", group="Display")

    def init(self):
        source = self.close if self.source == "close" else self.hl2
        if self.average_kind is AverageKind.EMA:
            self.average = self.ta.ema(source, length=self.length)
        else:
            self.average = self.ta.sma(source, length=self.length)
        # Runtime values are Enum and Color objects; derived colors do not mutate the read-only Input.
        self.background = self.line_color.with_transparency(85)
        self.plotting.line(self.average, title=self.average_kind.value, color=self.line_color)
        self.plotting.level(self.reference_price, title="Reference price")
        self.log.info(f"Moving average={self.average_kind.name}, session={self.session} (logged only; does not filter data)")

    def next(self):
        if not self.highlight or not self.average.valid[-1]:
            return
        # The example host supplies a UTC index; integer time values are not guessed to be seconds or local dates.
        current_ms = self.data_index[-1].timestamp() * 1000
        start_ms = self.start_time
        if current_ms < start_ms:
            return
        if self.close[-1] > self.average[-1] * self.multiplier:
            self.plotting.bg_color(self.background)
