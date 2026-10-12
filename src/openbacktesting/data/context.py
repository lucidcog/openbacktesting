"""Host-provided chart context; instrument specifications are bound separately."""

from dataclasses import dataclass
from zoneinfo import ZoneInfo

from openbacktesting.data.timeframe import Timeframe


@dataclass(frozen=True)
class DataContext:
    """Describe the existing market-data timeframe and shared timezone for charts, strategy calendars, and statistics.

    Timezone-aware market data is converted to this timezone before strategy construction; absolute instants and original data remain unchanged.
    Statistics group by local day boundaries; changing timezone requires a new run, and annualized metrics may differ.
    Provides no downloading, resampling, or exchange-calendar capability.
    """

    timeframe: Timeframe
    timezone: str

    def __post_init__(self):
        if not isinstance(self.timeframe, Timeframe):
            raise TypeError("timeframe must be a Timeframe")
        if not isinstance(self.timezone, str) or not self.timezone:
            raise TypeError("timezone must be a nonempty IANA timezone string")
        ZoneInfo(self.timezone)

    def snapshot(self) -> dict:
        """Return independent plain values without reusing mutable request objects."""
        return {"timeframe": self.timeframe.snapshot(), "timezone": self.timezone}
