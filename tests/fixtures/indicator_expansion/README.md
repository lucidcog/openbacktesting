# Independent indicator reference data

`quotes.csv`, `smi.json`, and `pmo.json` come from the [fixed Stock.Indicators commit](https://github.com/DaveSkender/Stock.Indicators/tree/e92f641d87ebf719b1f7a5a58744b8db781a2ba3/tests/Library/TestData), with original numerical values preserved. The full Apache-2.0 license is in the adjacent LICENSE.stock-indicators. Expected results do not require installing or calling that library.

Tests hand-calculate other small cases from public formulas. State machines also check fixed expectations in AtrStopSeriesTests and VolatilityStopSeriesTests at that commit. Local Volatility Stop remains invalid before its first reversal, avoiding the upstream retrospective clearing of history.
