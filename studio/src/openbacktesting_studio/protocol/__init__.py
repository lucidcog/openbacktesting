"""Studio-owned, strict versioned messages; core exports retain their own schemas."""

from pathlib import PurePosixPath
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, JsonValue, field_validator, model_validator

PROTOCOL_VERSION = 1
CONTAINER_VERSION = 1
CONFIG_VERSION = 1
PRESET_VERSION = 1
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def relative_path(value: str) -> str:
    """Use one portable path syntax before OS-specific containment checks."""
    path = PurePosixPath(value)
    if (
        not value
        or path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or ":" in value
        or "\x00" in value
        or str(path) != value
    ):
        raise ValueError("Expected a canonical workspace-relative path")
    return value


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)


class Versioned(Message):
    schemaVersion: Literal[1] = 1

    @field_validator("schemaVersion", mode="before")
    @classmethod
    def strict_version(cls, value):
        if type(value) is not int or value != 1:
            raise ValueError("Unsupported schema version")
        return value


class InputRequest(Message):
    schemaVersion: str
    schemaHash: str
    values: dict[str, JsonValue] = Field(default_factory=dict)


class Preset(Versioned):
    name: str = Field(min_length=1, max_length=120)
    inputs: InputRequest
    settings: dict[str, JsonValue] = Field(default_factory=dict)


class TimeframeConfig(Message):
    unit: Literal["second", "minute", "day", "week", "month"]
    multiplier: int = Field(gt=0)


class InstrumentConfig(Message):
    symbol: str = Field(min_length=1)
    quantity_step: float = Field(default=1, gt=0)
    min_quantity: float | None = Field(default=None, gt=0)
    price_tick: float | None = Field(default=None, gt=0)
    min_notional: float = Field(default=0, ge=0)
    currency: str | None = None


class DataProfile(Versioned):
    name: str = Field(min_length=1, max_length=120)
    kind: Literal["sample", "csv", "loader"]
    sample: Literal["GOOG", "BTCUSD", "EURUSD"] | None = None
    path: str | None = None
    function: str | None = None
    columns: dict[str, str] = Field(default_factory=dict)
    timeColumn: str | None = None
    timeUnit: Literal["s", "ms", "us", "ns"] | None = None
    sourceTimezone: str | None = None
    timezone: str
    timeframe: TimeframeConfig
    instrument: InstrumentConfig
    start: str | None = None
    end: str | None = None
    parameters: dict[str, JsonValue] = Field(default_factory=dict)
    resources: list[str] = Field(default_factory=list)

    @field_validator("path")
    @classmethod
    def path_valid(cls, value):
        return relative_path(value) if value is not None else None

    @field_validator("resources")
    @classmethod
    def resources_valid(cls, value):
        return [relative_path(item) for item in value]

    @field_validator("timezone", "sourceTimezone")
    @classmethod
    def timezone_valid(cls, value):
        if value is not None:
            try:
                ZoneInfo(value)
            except ZoneInfoNotFoundError as error:
                raise ValueError("Unknown timezone") from error
        return value

    @model_validator(mode="after")
    def source_valid(self):
        if self.kind == "sample":
            if self.sample is None or self.path is not None or self.function is not None:
                raise ValueError("Sample data requires a sample name and no file or loader")
        elif self.path is None or self.sample is not None:
            raise ValueError("File data requires a path and no sample name")
        if self.kind == "csv" and (not self.timeColumn or self.function is not None):
            raise ValueError("CSV requires a time column and no loader function")
        if self.kind == "loader" and (not self.function or not self.function.isidentifier()):
            raise ValueError("Loader requires an explicit function name")
        return self


class FileWrite(Message):
    path: str
    baseRevision: Hash
    content: str

    _path = field_validator("path")(relative_path)


class SourceRequest(Message):
    path: str
    revision: Hash
    roots: list[str] = Field(default_factory=lambda: ["."])
    resources: list[str] = Field(default_factory=list)

    _path = field_validator("path")(relative_path)

    @field_validator("roots", "resources")
    @classmethod
    def paths_valid(cls, value):
        return [relative_path(item) for item in value]


class RunRequest(Message):
    source: SourceRequest
    inputs: InputRequest
    settings: dict[str, JsonValue] = Field(default_factory=dict)
    data: DataProfile
    idempotencyKey: str = Field(min_length=1, max_length=128)
    parentRunId: str | None = None


class ArtifactEntry(Message):
    path: str
    sha256: Hash
    size: int = Field(ge=0)

    _path = field_validator("path")(relative_path)


class RunManifest(Versioned):
    runId: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,128}$")
    status: Literal["queued", "running", "cancelling", "succeeded", "failed", "cancelled"]
    requiredFeatures: list[str] = Field(default_factory=list)
    provenance: dict[str, JsonValue]
    artifacts: list[ArtifactEntry]
    diagnostics: list[dict[str, JsonValue]] = Field(default_factory=list)

    @field_validator("requiredFeatures")
    @classmethod
    def supported_features(cls, values):
        if values:
            raise ValueError("Unknown required container features")
        return values

    @model_validator(mode="after")
    def unique_paths(self):
        paths = [entry.path for entry in self.artifacts]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate artifact paths")
        return self


class ErrorResponse(Message):
    code: str
    message: str
    fieldErrors: dict[str, list[str]] = Field(default_factory=dict)
    details: dict[str, JsonValue] = Field(default_factory=dict)
    requestId: str


SCHEMAS = {
    "data-profile": DataProfile,
    "preset": Preset,
    "run-request": RunRequest,
    "run-manifest": RunManifest,
    "file-write": FileWrite,
    "error": ErrorResponse,
}


class SearchDomain(Message):
    kind: Literal["values", "range"]
    values: list[JsonValue] = Field(default_factory=list, max_length=100000)
    start: int | str | None = None
    stop: int | str | None = None
    step: int | str | None = None

    @model_validator(mode="after")
    def domain_valid(self):
        if self.kind == "values":
            if not self.values or any(
                value is not None for value in (self.start, self.stop, self.step)
            ):
                raise ValueError("Choose explicit values or a numeric range")
        elif self.values or any(value is None for value in (self.start, self.stop, self.step)):
            raise ValueError("A range requires start, stop and step")
        return self


class OptimizationRequest(Versioned):
    run: RunRequest
    search: dict[str, SearchDomain] = Field(min_length=1)
    constraint: str | None = Field(default=None, pattern=r"^[a-zA-Z_]\w*$")


class OptimizationQuery(Message):
    @field_validator("order_by", "filters", mode="before")
    @classmethod
    def json_tuples(cls, value):
        return (
            [tuple(item) if isinstance(item, list) else item for item in value]
            if isinstance(value, list)
            else value
        )

    order_by: list[tuple[str, Literal["asc", "desc"]]] = Field(default_factory=list)
    filters: list[tuple[str, Literal["eq", "ne", "lt", "le", "gt", "ge", "status"], JsonValue]] = (
        Field(default_factory=list)
    )
    fields: list[str] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=1000)
    cursor: str | None = None


SCHEMAS.update(
    {"optimization-request": OptimizationRequest, "optimization-query": OptimizationQuery}
)
