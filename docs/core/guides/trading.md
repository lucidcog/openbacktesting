# Orders, matching, and positions

0.2 supports orders in asset units, notional amounts, and equity percentages, using an independent execution ledger. `buy(qty=2)` means buying two units; a returned Order only confirms request registration, while final status and Fill identify execution results. See the [trading reference](../reference/trading.md) for fields.

## Units and budgets

Import `InstrumentSpec` from `openbacktesting.broker`. Defaults are `quantity_step=1`, minimum quantity equal to the step, `price_tick=None`, and `min_notional=0`. symbol/currency are labels without exchange-rate conversion. With `quantity_step=0.001`, `qty=0.1` always denotes one-tenth of an asset unit; market data and indicators are not scaled.

Direct quantities and limit/stop/sl/tp must satisfy explicit grids. Amounts/percentages, default fixed quantities, and sizing helpers may round toward zero. OHLC must be finite and positive, with an increasing unique index; configured tick grids also apply to market data. Data `pip` is not an exchange rule. Reduce-only exits may close residual holdings below the minimum opening notional.

`openbacktesting.strategy.sizing` supplies pure functions returning frozen `SizingDecision(qty, reference_price, estimated_cost, reason, budget)`:

| Function | Budget meaning |
| -------- | -------------- |
| `fixed_quantity` | Fixed asset quantity rounded toward zero |
| `equity_fraction` | Current equity times a fraction as a notional budget, shared by quantity and per-unit costs without margin amplification |
| `stop_risk` | Equity times risk fraction divided by stop distance plus per-unit round-trip costs |

Callers supply `cost_per_unit` estimates, which do not guarantee future fees or fill prices. Zero-quantity decisions include minimum-quantity/notional reasons and should be skipped. Nonpositive equity, wrong stop direction, and zero distance raise errors. With equity 10000, risk fraction 0.01, entry 100, stop 95, and zero costs, the plan is 20 units; gaps can still cause losses exceeding 100.

## Order sizing and defaults

Ordinary `buy/sell` accepts mutually exclusive `qty`, `amount`, and `percent`:

```python
self.buy(qty=0.2)        # Actual asset quantity, strictly matching the instrument step.
self.buy(amount=2000)    # Notional in account settlement currency, excluding fees.
self.buy(percent=20)     # 20% of request-time equity, not available cash or a target position.
self.sell(qty=0.2, reduce_only=True)
```

All three must be positive finite numbers, neither bool nor explicit None; percent range is (0,100]. Multiple sizing arguments raise an error without precedence. Defaults apply only when all three are omitted. `reduce_only=True` requires explicit qty, rejecting amounts, percentages, and defaults. Ordinary opposite-side order sizes are incremental and do not automatically add the existing position.

Authors combine `default_qty_type=QuantityType.FIXED` or `QuantityType.PERCENT_OF_EQUITY` with `default_qty_value`, importing enums from the package root. Default None requires explicit sizing. Equity quantity uses percentages (0,100], where 20 means 20%. With `@backtest(default_qty_type=QuantityType.PERCENT_OF_EQUITY, default_qty_value=20)`, `self.buy()` uses the default 20%, while `self.buy(amount=500)` overrides it. Host type changes require a value too; None can clear quantity. Low-level `Backtest` retains `DefaultOrderSize("fixed", value)` and `DefaultOrderSize("equity_fraction", value)`, with the latter using fractions (0,1].

Amount/percentage budgets convert at request-time Close and equity during allowed submission phases. Limit/stop orders also use Close, without margin amplification, deduction for pending orders, or fee reserves. The framework rounds toward zero by instrument step and rejects zero quantities or insufficient notional before registration, with reasons including below_min_quantity/below_min_notional. Explicit qty strictly validates grids without silent rounding; default fixed quantities may round. Failure neither cancels original orders nor changes ledgers. Quantities are not recalculated while awaiting execution. Fees, slippage, and gaps can cause insufficient-funds rejection; amount does not guarantee executed notional equals budget.

Ordinary read-only `order.sizing` is an `OrderSizingSnapshot` frozen before submission, retaining mode, source, value, equity, reference_price, budget, and qty. source distinguishes explicit/default; qty-mode budget is None. Reduce-only snapshots retain requested quantity even if less executes. Internal targets, lot exits, protection, and terminal liquidation have sizing=None. Results link `_order_sizing` by order_id; see the [results guide](results.md).

`equity_fraction` and `stop_risk` remain independent budget-analysis and custom-cost tools; ordinary orders need not call them first. `order_target_percent(target=0.2)`, `set_trailing_stop(percent=0.1)`, legacy sizing tools, and low-level equity_fraction defaults retain fractional units. Only new order percent and author default quantities use percentages. See the [fractional-sizing author script](../../../examples/strategies/fractional_sizing.py) and [host overrides/rejection example](../../../examples/advanced/strategy_settings.py).

## Requests, fills, and lots

- Order has stable `order_id`, immutable `request`, and frozen `snapshot`. States are Submitted, Accepted, PartiallyFilled, Filled, Canceled, Expired, and Rejected. Terminal states cannot reopen; repeated terminal cancellation is idempotent. Accepted reserves no funds.
- Every actual execution produces one Fill and charges fees once. A reversal Fill may close multiple FIFO lots and open one residual lot. Ordinary reversals preflight the whole order; rejection must not leave partial closure.
- Trade is an independently manageable entry lot with `trade_id` and entry Fill identity. Partial exits preserve lot identity and produce independent closed fragments; fixed entry fees are apportioned by exit quantity, with residual fees assigned to the last fragment without calling the entry-fee model again.
- `sell(qty=10, reduce_only=True)` reduces at most available quantity, records Partial for residual quantity, then cancels it. No reducible position cancels as `no_position`. Hedged exits must bind a lot.

`Trade.close(qty=...)` and `Trade.close(portion=...)` are mutually exclusive, defaulting to complete closure. Portions round toward zero; rounding to zero raises an error. `close_position()` and `position.close()` submit exits per lot and return ordered tuples, empty when flat. `self.close` remains a market-data handle.

`order_target_quantity(target=...)`, `order_target_value(target=...)`, and `order_target_percent(target=...)` support netting mode only. All explicitly accept keyword-only target, limit, stop, sl, tp, tag, reduce_only, expires_at, and valid_bars, without positional arguments or conditions dictionaries. value/percent converts using request-time Close/equity and fixes quantity. Unfinished orders with identical targets/conditions are reused; changed targets cancel prior orders and compute differences from actual holdings. Ordinary entry/manual-exit pending orders raise `conflicting_pending_order`; protective orders may coexist. Target fills still check buying power and do not guarantee the target weight after gaps.

Price domains/grids, expiry, tags, and strict-bool reduce_only are validated before returning None for zero differences, deduplicating targets, or canceling prior orders. Omitted optional arguments equal explicit None/False; invalid replacements preserve original targets. SL/TP relationships are checked by actual trade direction only for nonzero differences. Valid zero differences may cancel old targets without constructing zero-quantity orders.

## Account invariants

One asset, one settlement currency, linear margin, contract multiplier 1:

- balance = initial balance + realized gross price profit/loss − all actual fees.
- equity = balance + unrealized gross price profit/loss.
- margin_used = gross notional exposure × margin; available margin is nonnegative.
- When finally flat, equity = balance = initial balance + all closed-fragment net profit/loss.

`account` is a frozen snapshot; balance is not securities-settlement cash. `position.snapshot` provides net/gross/long/short quantities, leg-average prices, gross/net profit/loss, and remaining entry fees. Equal opposing positions have zero net quantity but `bool(position)` remains true. Hedged or flat positions have no unified cost, with `return_fraction=None`. `Trade.pl` and `Position.pl` are net profit/loss, including remaining entry fees for active holdings. `return_fraction` is fractional, as is statistical `ReturnPct`.

`allow_short=False` only prevents new shorts; optional `max_gross_exposure` limits gross notional/equity. These opening restrictions do not block valid reductions. Gap-induced insolvency cancels pending orders and liquidates, retaining actual negative equity; liquidation errors propagate without fabricated success.

## Lifecycle and termination

`init()` precomputes indicators; `on_start()` and `on_finish(summary)` each run once and cannot trade. Each normal bar first processes existing orders, then dispatches a closed batch of `on_order/on_fill` notifications, then calls `next()` from the first bar; single-bar input also gets one call. Invalid indicators do not skip `next()`. Order notifications, protection, and trailing updates retain execution phases. Orders submitted in notifications execute no earlier than the next bar without recursive matching. Exceptions invoke the finish hook; if it also fails, the original exception is retained with a note.

| Configuration | Behavior |
| ------------- | -------- |
| `execution_timing=ExecutionTiming.NEXT_OPEN` | Default; requests submitted by the current strategy process no earlier than the next bar |
| `execution_timing=ExecutionTiming.SAME_CLOSE` | New unconditional market orders from `next()` process once at current Close; new limit/protective orders cannot use already-occurring current High/Low |
| `end_policy=EndPolicy.MARK_TO_MARKET` | Default; cancel pending orders, retain open lots valued at final Close |
| `end_policy=EndPolicy.CLOSE_AT_LAST_CLOSE` | Cancel pending orders, then synthetically liquidate only actual holdings at final Close, charging costs normally |

These are author enum forms; low-level Backtest retains corresponding lowercase strings. Termination does not rerun final-bar matching. Entries submitted in the last `next()` without reaching execution do not fill artificially. A separate terminal snapshot does not overwrite normal-bar exposure observations.

## Expiry, groups, and costs

Default expiry is GTC. `valid_bars=n` permits execution on bars 1 through n after submission, expiring first on the following bar. `expires_at` and market-data indexes must be timezone-aware; equality with the expiry instant means expired. The two options are mutually exclusive. Protective orders are GTC.

`submit_oco(first=OrderRequest(...), second=OrderRequest(...))` accepts two named entry requests; import OrderRequest from openbacktesting.broker. side is required, with exactly one explicit qty/amount/percent sizing mode rather than inherited defaults. Other fields are limit, stop, sl, tp, tag, expires_at, and valid_bars; unselected sizing attributes are None. Construction has no trading side effects and can occur in init or be reused across runs; tags freeze on construction.

```python
# Prepare in init without reading account or market data.
self.long_entry = OrderRequest(side="buy", percent=20, stop=105)
self.short_entry = OrderRequest(side="sell", amount=2000, stop=95)
# Submit in next; both members use the same account, Close, and instrument moment.
group = self.submit_oco(first=self.long_entry, second=self.short_entry)
```

Instrument grids, market timezone, and protective direction are validated at submission. Members resolve separately to fixed quantities; all validation precedes atomic registration and snapshot publication. Failure of the second registers neither the first nor consumes order/group identities. Budgets are not split, cumulatively deducted, or reserved across members, and buying power remains independently checked at execution; mixed modes do not change phases.
Members may have the same or opposing sides. Filling, canceling, expiring, or rejecting either terminates the other. first wins same-bar dual triggers, recording `ambiguous_oco_bar`. Groups support historical queries and cancellation; canceling a protective group does not close positions automatically.

Initial `sl/tp` activates after actual entry. Protection for ordinary next-open market entries can inspect the remaining current-bar range; conditional and same-close entry protection waits until the next bar with a diagnostic. If both SL/TP are reachable in one bar, SL executes and `ambiguous_bracket_bar` is recorded, without claiming the actual intrabar order. Partial exits cancel and rebuild protection for remaining quantity.

`trade.set_trailing_stop(amount=...)` or `percent=...` replaces fixed SL and may retain TP. The old stop is checked first; then current Close tightens the stop monotonically for the next bar. Percentages apply directly to current price. `TrailingStrategy` ATR does not backfill future values and sets no protection before ATR warmup.

Authors declare fixed-distance/basis-point slippage through `slippage_type=SlippageType.FIXED/BPS` and nonnegative `slippage_value`, with 0 disabling it. spread affects each buy/sell execution. Low-level `Slippage("none")`, `Slippage("fixed", value)`, and `Slippage("bps", value)` provide deterministic slippage. Cost-adjusted prices round upward for buys and downward for sells to ticks without crossing limits. Ordinary market/stop fills stay within current High/Low; same-close and terminal synthetic fills may have cost prices outside the bar range. Fee functions must be pure and return finite values; rebates may be negative, without reliance on callback side effects.

Ordinary buy/sell remain keyword-only, and reduce_only must be bool. tag may contain pure JSON values, including nested dictionaries; it is optional metadata rather than an order-conditions dictionary. Author OrderRequest rejects reduce_only/trade_id/tag_json. Registered request is a read-only normalized observation consistent with [result tables](results.md).

## Commission modes and advanced composite fees

Authors use `commission_type=CommissionType.PERCENT/CASH_PER_ORDER/CASH_PER_CONTRACT` and `commission_value`. Percentage 0.2 means 0.2% of executed notional, with range [-10,10); other modes use nonnegative account amounts per actual Fill or asset unit. A reversal Fill still pays one fixed fee, apportioned afterward by quantity. The author entry point enables one mode at a time.

Low-level `Backtest` uses `Commission(fixed=0.0, relative=0.0, per_unit=0.0)` imported from openbacktesting.broker. Each actual Fill pays `fixed + abs(qty) * price * relative + abs(qty) * per_unit`. Fixed and per-unit amounts are nonnegative; relative is [-0.1,0.1). Values must be finite and not bool. relative=0.002 means 0.2%, and per_unit is a fee per actual asset unit with contract multiplier still 1.

Low-level numeric and two-element tuple commissions remain available. Buying-power preflight does not deduct fees; actual Fill charges once, with reversals and partial exits retaining allocation. Every liquidation path uses the same formula. snapshot/from_snapshot strictly restores kind=linear, version=1, and all three fields, rejecting unknown fields/versions. Arbitrary callables remain low-level only with nonreconstructable diagnostics. See the [settings tutorial](../../../examples/advanced/strategy_settings.py) for composite fees and [per-unit fee example](../../../examples/strategies/trading_lifecycle.py) for author modes.

## Examples and validation

| Capability | Runnable example | Validation |
| ---------- | ---------------- | ---------- |
| States, fees, accounts, lifecycle, termination | [trading_lifecycle.py](../../../examples/strategies/trading_lifecycle.py) | `test_order_api.py`, `test_trading_core.py`, `test_trading_regressions.py`, `test_examples.py` |
| Three modes, default overrides, snapshots, named targets, reduce-only | [fractional_sizing.py](../../../examples/strategies/fractional_sizing.py) | Same tests |
| Expiry, mixed-sizing OCO, protection, trailing, costs | [managed_orders.py](../../../examples/strategies/managed_orders.py) | Same tests |

Run through the [example entry point](../examples.md). Trading records are generated directly by the Python engine.

## Explicit price rounding and closed fragments

`instrument.round_price_to_tick(value)` requires finite positive price and explicit `price_tick`, rounding to the nearest decimal tick with exact halves upward. Zero, overflow, or inability to represent the decimal grid exactly as float is rejected. The result passes the existing `price` validator again. This tool serves author candidate prices only, without automatically correcting orders or changing existing directional rounding for fills/protection.

`self.closed_trade_stats` returns a frozen `broker.ClosedTradeStats` snapshot. It counts closed fragments rather than unique `trade_id`, counting partial exits separately. Net profit/loss includes allocated entry and exit fees; rebates retain their actual sign. `win_count/loss_count/even_count` partitions strictly positive, negative, and zero net results. `winning_profit` sums positive net results, `losing_amount` is nonnegative loss magnitude, `net_profit` is their difference, `average_profit` divides net profit by fragment count, and `win_rate` is a 0–1 fraction. Empty amounts/counts are zero, with mean and win rate None.

Statistics update incrementally after closing-fee allocation without scanning history on reads. Unrealized results and unallocated open-lot entry fees do not enter early. Exits submitted in same_close next still see pre-fill facts; subsequent fill notifications and on_finish can read completed results. Notifications dispatch after a fill batch completes, so every notification in that batch reads the latest cumulative state rather than per-event historical snapshots. Saved snapshots do not change with later fills or Trade-object modifications; repeated runs are independent. The property is reserved and cannot be overridden. See [pure-value helpers](../../../examples/strategies/local_value_helpers.py) and [closed statistics](../../../examples/strategies/closed_trade_statistics.py).
