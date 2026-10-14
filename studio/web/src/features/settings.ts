import type { Description, Value } from './inputs'
export const settingChoices: Record<string, string[]> = { commission_type: ['percent', 'cash_per_order', 'cash_per_contract'], default_qty_type: ['fixed', 'percent_of_equity'], slippage_type: ['bps', 'fixed'], execution_timing: ['next_open', 'same_close'], end_policy: ['mark_to_market', 'close_at_last_close'] }
/** Mirror the core's BacktestSettings constraints for immediate form feedback. */
export function settingErrors(schema: Description, overrides: Record<string, Value | null>) {
  const effective = { ...schema.backtest.settings, ...overrides }, errors: Record<string, string> = {}
  for (const [key, baseline] of Object.entries(schema.backtest.settings)) {
    const value = effective[key]
    if (settingChoices[key]) { if (!settingChoices[key].includes(String(value))) errors[key] = 'Choose an available option'; continue }
    if (typeof baseline === 'boolean') { if (typeof value !== 'boolean') errors[key] = 'Choose true or false'; continue }
    if (value === null && ['default_qty_value', 'max_gross_exposure'].includes(key)) continue
    if (typeof value !== 'number' || !Number.isFinite(value)) { errors[key] = 'Enter a finite number'; continue }
    if (['cash', 'margin', 'default_qty_value', 'max_gross_exposure'].includes(key) && value <= 0) errors[key] = 'Must be greater than zero'
    if (key === 'margin' && value > 1) errors[key] = 'Must be at most 1'
    if (key === 'spread' && (value < 0 || value >= 1)) errors[key] = 'Must be in [0, 1)'
    if (key === 'risk_free_rate' && (value <= -1 || value >= 1)) errors[key] = 'Must be in (-1, 1)'
    if (key === 'commission_value' && (effective.commission_type === 'percent' ? value < -10 || value >= 10 : value < 0)) errors[key] = effective.commission_type === 'percent' ? 'Must be in [-10, 10)' : 'Must not be negative'
    if (key === 'slippage_value' && value < 0) errors[key] = 'Must not be negative'
    if (key === 'default_qty_value' && effective.default_qty_type === 'percent_of_equity' && value > 100) errors[key] = 'Must be at most 100 percent'
  }
  return errors
}
