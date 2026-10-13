# Configure strategy parameters

Declare fields with `inputs.int`, `float`, `bool`, `string`, `price`, `time`, `session`, `color`, or `enum`. Each needs a unique title and default. Read it in the strategy as a normal `self` attribute.

The [complete inputs example](../reference/inputs.md#declare-and-override-parameters) shows declaration, execution, and overrides.

## Select the configuration path

| Caller | How to supply values |
| --- | --- |
| Python script or notebook | `bt.run(length=30)` using field names |
| Application with a settings form | `inputs.describe(MyStrategy)` then a title-based request to `bt.run_inputs(request)` |
| Decorated strategy file | Pass that request to `runtime.run` |
| Grid optimization | `bt.optimize(length=[10, 20, 30])` using field names |
| Saved experiment | `runtime.optimize(..., {"Length": Values([10, 20, 30])}, ...)` using titles |

`inputs.request_for(MyStrategy, {"length": 30})` constructs a title-based request from native Python overrides. Changing a declaration invalidates old request hashes; rediscover before resubmitting.

For numeric fields, choose either options or bounds/step. Invalid values fail before the strategy starts. Colors become `Color` objects; enum fields become enum members. Session strings describe a setting but do not automatically filter your bars.

[Input types and all arguments](../reference/inputs.md) · [Runtime](../reference/runtime.md)
