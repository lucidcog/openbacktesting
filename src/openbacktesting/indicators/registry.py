"""已审核的显式计算绑定；注册不会自动发现或开放供应商函数。"""

from collections.abc import Callable
from dataclasses import dataclass
from inspect import Parameter as SignatureParameter
from inspect import signature

from .candles.cdl_doji import compute as cdl_doji
from .candles.cdl_engulfing import compute as cdl_engulfing
from .candles.cdl_eveningstar import compute as cdl_eveningstar
from .candles.cdl_hammer import compute as cdl_hammer
from .candles.cdl_harami import compute as cdl_harami
from .candles.cdl_inside import compute as cdl_inside
from .candles.cdl_marubozu import compute as cdl_marubozu
from .candles.cdl_morningstar import compute as cdl_morningstar
from .candles.cdl_shootingstar import compute as cdl_shootingstar
from .candles.cdl_z import compute as cdl_z
from .candles.ha import compute as ha
from .common import SPECS
from .cycles.dsp import compute as dsp
from .cycles.ebsw import compute as ebsw
from .cycles.ht_dcperiod import compute as ht_dcperiod
from .cycles.ht_dcphase import compute as ht_dcphase
from .cycles.ht_phasor import compute as ht_phasor
from .cycles.ht_sine import compute as ht_sine
from .cycles.ht_trendmode import compute as ht_trendmode
from .cycles.msw import compute as msw
from .momentum.ac import compute as ac
from .momentum.ao import compute as ao
from .momentum.apo import compute as apo
from .momentum.bias import compute as bias
from .momentum.bop import compute as bop
from .momentum.brar import compute as brar
from .momentum.cci import compute as cci
from .momentum.cfo import compute as cfo
from .momentum.cg import compute as cg
from .momentum.cmo import compute as cmo
from .momentum.coppock import compute as coppock
from .momentum.crsi import compute as crsi
from .momentum.cti import compute as cti
from .momentum.dm import compute as dm
from .momentum.er import compute as er
from .momentum.eri import compute as eri
from .momentum.fisher import compute as fisher
from .momentum.fosc import compute as fosc
from .momentum.gator import compute as gator
from .momentum.ibs import compute as ibs
from .momentum.inertia import compute as inertia
from .momentum.kdj import compute as kdj
from .momentum.kst import compute as kst
from .momentum.lrsi import compute as lrsi
from .momentum.macd import compute as macd
from .momentum.macdext import compute as macdext
from .momentum.macdfix import compute as macdfix
from .momentum.mom import compute as mom
from .momentum.pgo import compute as pgo
from .momentum.pmo import compute as pmo
from .momentum.po import compute as po
from .momentum.ppo import compute as ppo
from .momentum.psl import compute as psl
from .momentum.pvo import compute as pvo
from .momentum.qqe import compute as qqe
from .momentum.rci import compute as rci
from .momentum.rmi import compute as rmi
from .momentum.roc import compute as roc
from .momentum.rocp import compute as rocp
from .momentum.rocr import compute as rocr
from .momentum.rocr100 import compute as rocr100
from .momentum.rsi import compute as rsi
from .momentum.rsx import compute as rsx
from .momentum.rvgi import compute as rvgi
from .momentum.slope import compute as slope
from .momentum.smc_sweep import compute as smc_sweep
from .momentum.smi import compute as smi
from .momentum.smi_stochastic import compute as smi_stochastic
from .momentum.squeeze import compute as squeeze
from .momentum.squeeze_pro import compute as squeeze_pro
from .momentum.stc import compute as stc
from .momentum.stoch import compute as stoch
from .momentum.stochf import compute as stochf
from .momentum.stochrsi import compute as stochrsi
from .momentum.td_seq import compute as td_seq
from .momentum.trix import compute as trix
from .momentum.trixh import compute as trixh
from .momentum.tsi import compute as tsi
from .momentum.uo import compute as uo
from .momentum.vwmacd import compute as vwmacd
from .momentum.wavetrend import compute as wavetrend
from .momentum.willr import compute as willr
from .overlap.alligator import compute as alligator
from .overlap.alma import compute as alma
from .overlap.anchored_vwap import compute as anchored_vwap
from .overlap.anchored_vwap_bands import compute as anchored_vwap_bands
from .overlap.avgprice import compute as avgprice
from .overlap.dema import compute as dema
from .overlap.ema import compute as ema
from .overlap.frama import compute as frama
from .overlap.fwma import compute as fwma
from .overlap.hilo import compute as hilo
from .overlap.hl2 import compute as hl2
from .overlap.hlc3 import compute as hlc3
from .overlap.hma import compute as hma
from .overlap.ht_trendline import compute as ht_trendline
from .overlap.hwma import compute as hwma
from .overlap.ichimoku import compute as ichimoku
from .overlap.jma import compute as jma
from .overlap.kama import compute as kama
from .overlap.linreg import compute as linreg
from .overlap.linregangle import compute as linregangle
from .overlap.linregintercept import compute as linregintercept
from .overlap.linregslope import compute as linregslope
from .overlap.ma import compute as ma
from .overlap.ma_envelopes import compute as ma_envelopes
from .overlap.mama import compute as mama
from .overlap.mavp import compute as mavp
from .overlap.mcgd import compute as mcgd
from .overlap.medprice import compute as medprice
from .overlap.midpoint import compute as midpoint
from .overlap.midprice import compute as midprice
from .overlap.mmar import compute as mmar
from .overlap.ohlc4 import compute as ohlc4
from .overlap.pwma import compute as pwma
from .overlap.rainbow import compute as rainbow
from .overlap.rma import compute as rma
from .overlap.sinwma import compute as sinwma
from .overlap.sma import compute as sma
from .overlap.sma import compute_pandas as sma_pandas
from .overlap.ssf import compute as ssf
from .overlap.supertrend import compute as supertrend
from .overlap.swma import compute as swma
from .overlap.t3 import compute as t3
from .overlap.tema import compute as tema
from .overlap.trima import compute as trima
from .overlap.tsf import compute as tsf
from .overlap.typprice import compute as typprice
from .overlap.vidya import compute as vidya
from .overlap.vwap import compute as vwap
from .overlap.vwma import compute as vwma
from .overlap.wcp import compute as wcp
from .overlap.wma import compute as wma
from .overlap.zlma import compute as zlma
from .performance.drawdown import compute as drawdown
from .performance.log_return import compute as log_return
from .performance.percent_return import compute as percent_return
from .statistics.beta import compute as beta
from .statistics.correl import compute as correl
from .statistics.entropy import compute as entropy
from .statistics.kurtosis import compute as kurtosis
from .statistics.mad import compute as mad
from .statistics.md import compute as md
from .statistics.median import compute as median
from .statistics.mode import compute as mode
from .statistics.quantile import compute as quantile
from .statistics.skew import compute as skew
from .statistics.stderr import compute as stderr
from .statistics.stdev import compute as stdev
from .statistics.variance import compute as variance
from .statistics.zscore import compute as zscore
from .trend.adx import compute as adx
from .trend.adxr import compute as adxr
from .trend.amat import compute as amat
from .trend.aroon import compute as aroon
from .trend.atr_stop import compute as atr_stop
from .trend.chop import compute as chop
from .trend.cksp import compute as cksp
from .trend.cpr import compute as cpr
from .trend.decay import compute as decay
from .trend.decreasing import compute as decreasing
from .trend.dpo import compute as dpo
from .trend.dx import compute as dx
from .trend.edecay import compute as edecay
from .trend.increasing import compute as increasing
from .trend.long_run import compute as long_run
from .trend.minus_dm import compute as minus_dm
from .trend.pivot_points import compute as pivot_points
from .trend.pivothigh import compute as pivothigh
from .trend.pivotlow import compute as pivotlow
from .trend.plus_dm import compute as plus_dm
from .trend.pmax import compute as pmax
from .trend.psar import compute as psar
from .trend.qstick import compute as qstick
from .trend.sarext import compute as sarext
from .trend.short_run import compute as short_run
from .trend.tsignals import compute as tsignals
from .trend.ttm_trend import compute as ttm_trend
from .trend.vhf import compute as vhf
from .trend.volatility_stop import compute as volatility_stop
from .trend.vortex import compute as vortex
from .trend.xsignals import compute as xsignals
from .types import IndicatorError
from .utility.barssince import compute as barssince
from .utility.change import compute as change
from .utility.cross import compute as cross
from .utility.crossover import compute as crossover
from .utility.crossunder import compute as crossunder
from .utility.cum import compute as cum
from .utility.falling import compute as falling
from .utility.highest import compute as highest
from .utility.highestbars import compute as highestbars
from .utility.lowest import compute as lowest
from .utility.lowestbars import compute as lowestbars
from .utility.percentile_linear_interpolation import compute as percentile_linear_interpolation
from .utility.percentile_nearest_rank import compute as percentile_nearest_rank
from .utility.percentrank import compute as percentrank
from .utility.range import compute as range
from .utility.rising import compute as rising
from .utility.rolling_count import compute as rolling_count
from .utility.rolling_sum import compute as rolling_sum
from .utility.running_max import compute as running_max
from .utility.running_min import compute as running_min
from .utility.shift import compute as shift
from .utility.valuewhen import compute as valuewhen
from .volatility.aberration import compute as aberration
from .volatility.accbands import compute as accbands
from .volatility.adr import compute as adr
from .volatility.atr import compute as atr
from .volatility.avolume import compute as avolume
from .volatility.bbands import compute as bbands
from .volatility.ce import compute as ce
from .volatility.cvi import compute as cvi
from .volatility.donchian import compute as donchian
from .volatility.hvol import compute as hvol
from .volatility.hwc import compute as hwc
from .volatility.kc import compute as kc
from .volatility.massi import compute as massi
from .volatility.natr import compute as natr
from .volatility.pdist import compute as pdist
from .volatility.rvi import compute as rvi
from .volatility.starc import compute as starc
from .volatility.thermo import compute as thermo
from .volatility.true_range import compute as true_range
from .volatility.ui import compute as ui
from .volume.ad import compute as ad
from .volume.adosc import compute as adosc
from .volume.aobv import compute as aobv
from .volume.cmf import compute as cmf
from .volume.efi import compute as efi
from .volume.emv import compute as emv
from .volume.eom import compute as eom
from .volume.iii import compute as iii
from .volume.kvo import compute as kvo
from .volume.marketfi import compute as marketfi
from .volume.mfi import compute as mfi
from .volume.nvi import compute as nvi
from .volume.obv import compute as obv
from .volume.pvi import compute as pvi
from .volume.pvol import compute as pvol
from .volume.pvr import compute as pvr
from .volume.pvt import compute as pvt
from .volume.rvol import compute as rvol
from .volume.vfi import compute as vfi
from .volume.vosc import compute as vosc
from .volume.wad import compute as wad
from .volume.wvad import compute as wvad

NATIVE = "pandas-ta-classic.native"
PANDAS = "pandas.sma"
LOCAL = "openbacktesting.numpy"


@dataclass(frozen=True)
class Binding:
    compute: Callable
    implementation_version: str


def build_bindings(entries, specs):
    available = {spec.id: spec for spec in specs if spec.status == "available"}
    bindings = {}
    for indicator, backend, compute, implementation_version in entries:
        key = (indicator, backend)
        if key in bindings or indicator not in available:
            raise ValueError(f"重复或未经审核的指标绑定: {key}")
        if backend not in (NATIVE, PANDAS, LOCAL) or backend == PANDAS and indicator != "ta.sma":
            raise ValueError(f"未经审核的后端: {key}")
        spec = available[indicator]
        expected = set(spec.inputs) | dict(spec.parameters).keys() | dict(spec.fixed).keys()
        if backend == NATIVE:
            expected.add("talib")
        parameters = signature(compute).parameters
        if set(parameters) != expected or any(
            p.kind != SignatureParameter.KEYWORD_ONLY or p.default != SignatureParameter.empty
            for p in parameters.values()
        ):
            raise ValueError(f"指标绑定签名与目录不一致: {key}")
        module = f"openbacktesting.indicators.{spec.category}.{spec.id.removeprefix('ta.')}"
        if (
            compute.__module__ != module
            or not isinstance(implementation_version, str)
            or not implementation_version
        ):
            raise ValueError(f"指标归属或实现版本非法: {key}")
        bindings[key] = Binding(compute, implementation_version)
    missing = {
        name for name, spec in available.items() if (name, spec.default_backend) not in bindings
    }
    if missing:
        raise ValueError(f"可用指标缺少默认实现: {sorted(missing)}")
    return bindings


ENTRIES = (
    ("ta.highest", LOCAL, highest, "1"),
    ("ta.lowest", LOCAL, lowest, "1"),
    ("ta.highestbars", LOCAL, highestbars, "1"),
    ("ta.lowestbars", LOCAL, lowestbars, "1"),
    ("ta.rolling_sum", LOCAL, rolling_sum, "1"),
    ("ta.range", LOCAL, range, "1"),
    ("ta.percentrank", LOCAL, percentrank, "1"),
    ("ta.rolling_count", LOCAL, rolling_count, "1"),
    ("ta.cum", LOCAL, cum, "1"),
    ("ta.running_max", LOCAL, running_max, "1"),
    ("ta.running_min", LOCAL, running_min, "1"),
    ("ta.change", LOCAL, change, "1"),
    ("ta.shift", LOCAL, shift, "1"),
    ("ta.percentile_nearest_rank", LOCAL, percentile_nearest_rank, "1"),
    ("ta.percentile_linear_interpolation", LOCAL, percentile_linear_interpolation, "1"),
    ("ta.cross", LOCAL, cross, "1"),
    ("ta.crossover", LOCAL, crossover, "1"),
    ("ta.crossunder", LOCAL, crossunder, "1"),
    ("ta.barssince", LOCAL, barssince, "1"),
    ("ta.valuewhen", LOCAL, valuewhen, "1"),
    ("ta.rising", LOCAL, rising, "1"),
    ("ta.falling", LOCAL, falling, "1"),
    ("ta.pivothigh", LOCAL, pivothigh, "1"),
    ("ta.pivotlow", LOCAL, pivotlow, "1"),
    ("ta.smi_stochastic", LOCAL, smi_stochastic, "1"),
    ("ta.crsi", LOCAL, crsi, "1"),
    ("ta.pmo", LOCAL, pmo, "1"),
    ("ta.rmi", LOCAL, rmi, "1"),
    ("ta.alligator", LOCAL, alligator, "1"),
    ("ta.gator", LOCAL, gator, "1"),
    ("ta.atr_stop", LOCAL, atr_stop, "1"),
    ("ta.volatility_stop", LOCAL, volatility_stop, "1"),
    ("ta.ma_envelopes", LOCAL, ma_envelopes, "1"),
    ("ta.starc", LOCAL, starc, "1"),
    ("ta.ac", LOCAL, ac, "1"),
    ("ta.ibs", LOCAL, ibs, "1"),
    ("ta.frama", LOCAL, frama, "1"),
    ("ta.wavetrend", LOCAL, wavetrend, "1"),
    ("ta.adr", LOCAL, adr, "1"),
    ("ta.rvol", LOCAL, rvol, "1"),
    ("ta.rci", LOCAL, rci, "1"),
    ("ta.iii", LOCAL, iii, "1"),
    ("ta.wvad", LOCAL, wvad, "1"),
    ("ta.pivot_points", LOCAL, pivot_points, "2"),
    ("ta.anchored_vwap", LOCAL, anchored_vwap, "1"),
    ("ta.anchored_vwap_bands", LOCAL, anchored_vwap_bands, "1"),
    ("ta.mode", LOCAL, mode, "1"),
    ("ta.cdl_doji", LOCAL, cdl_doji, "1"),
    ("ta.cdl_inside", NATIVE, cdl_inside, "1"),
    ("ta.cdl_engulfing", NATIVE, cdl_engulfing, "1"),
    ("ta.cdl_hammer", NATIVE, cdl_hammer, "1"),
    ("ta.cdl_shootingstar", NATIVE, cdl_shootingstar, "1"),
    ("ta.cdl_harami", NATIVE, cdl_harami, "1"),
    ("ta.cdl_morningstar", NATIVE, cdl_morningstar, "1"),
    ("ta.cdl_eveningstar", NATIVE, cdl_eveningstar, "1"),
    ("ta.cdl_marubozu", NATIVE, cdl_marubozu, "1"),
    ("ta.cdl_z", NATIVE, cdl_z, "1"),
    ("ta.ha", NATIVE, ha, "1"),
    ("ta.dsp", NATIVE, dsp, "1"),
    ("ta.ebsw", NATIVE, ebsw, "1"),
    ("ta.ht_dcperiod", NATIVE, ht_dcperiod, "1"),
    ("ta.ht_dcphase", NATIVE, ht_dcphase, "1"),
    ("ta.ht_phasor", NATIVE, ht_phasor, "1"),
    ("ta.ht_sine", NATIVE, ht_sine, "1"),
    ("ta.ht_trendmode", NATIVE, ht_trendmode, "1"),
    ("ta.msw", NATIVE, msw, "2"),
    ("ta.ao", NATIVE, ao, "1"),
    ("ta.apo", NATIVE, apo, "1"),
    ("ta.bias", NATIVE, bias, "1"),
    ("ta.bop", NATIVE, bop, "1"),
    ("ta.brar", NATIVE, brar, "1"),
    ("ta.cci", NATIVE, cci, "1"),
    ("ta.cfo", NATIVE, cfo, "1"),
    ("ta.cg", NATIVE, cg, "1"),
    ("ta.cmo", NATIVE, cmo, "1"),
    ("ta.coppock", NATIVE, coppock, "1"),
    ("ta.cti", NATIVE, cti, "1"),
    ("ta.dm", NATIVE, dm, "1"),
    ("ta.er", NATIVE, er, "1"),
    ("ta.eri", NATIVE, eri, "1"),
    ("ta.fisher", NATIVE, fisher, "1"),
    ("ta.fosc", NATIVE, fosc, "1"),
    ("ta.inertia", NATIVE, inertia, "1"),
    ("ta.kdj", NATIVE, kdj, "1"),
    ("ta.kst", NATIVE, kst, "1"),
    ("ta.lrsi", NATIVE, lrsi, "1"),
    ("ta.macd", NATIVE, macd, "1"),
    ("ta.macdext", NATIVE, macdext, "1"),
    ("ta.macdfix", NATIVE, macdfix, "1"),
    ("ta.mom", NATIVE, mom, "1"),
    ("ta.pgo", NATIVE, pgo, "1"),
    ("ta.po", NATIVE, po, "1"),
    ("ta.ppo", NATIVE, ppo, "1"),
    ("ta.psl", NATIVE, psl, "1"),
    ("ta.pvo", NATIVE, pvo, "1"),
    ("ta.qqe", NATIVE, qqe, "1"),
    ("ta.roc", NATIVE, roc, "1"),
    ("ta.rocp", NATIVE, rocp, "1"),
    ("ta.rocr", NATIVE, rocr, "1"),
    ("ta.rocr100", NATIVE, rocr100, "1"),
    ("ta.rsi", NATIVE, rsi, "1"),
    ("ta.rsx", NATIVE, rsx, "1"),
    ("ta.rvgi", NATIVE, rvgi, "1"),
    ("ta.slope", NATIVE, slope, "1"),
    ("ta.smc_sweep", NATIVE, smc_sweep, "1"),
    ("ta.smi", NATIVE, smi, "1"),
    ("ta.squeeze", NATIVE, squeeze, "2"),
    ("ta.squeeze_pro", NATIVE, squeeze_pro, "2"),
    ("ta.stc", NATIVE, stc, "1"),
    ("ta.stoch", NATIVE, stoch, "1"),
    ("ta.stochf", NATIVE, stochf, "1"),
    ("ta.stochrsi", NATIVE, stochrsi, "1"),
    ("ta.td_seq", NATIVE, td_seq, "1"),
    ("ta.trix", NATIVE, trix, "1"),
    ("ta.trixh", NATIVE, trixh, "1"),
    ("ta.tsi", NATIVE, tsi, "1"),
    ("ta.uo", NATIVE, uo, "1"),
    ("ta.vwmacd", NATIVE, vwmacd, "1"),
    ("ta.willr", NATIVE, willr, "1"),
    ("ta.alma", NATIVE, alma, "2"),
    ("ta.avgprice", NATIVE, avgprice, "1"),
    ("ta.dema", NATIVE, dema, "1"),
    ("ta.ema", NATIVE, ema, "1"),
    ("ta.fwma", NATIVE, fwma, "1"),
    ("ta.hilo", NATIVE, hilo, "1"),
    ("ta.hl2", NATIVE, hl2, "1"),
    ("ta.hlc3", NATIVE, hlc3, "1"),
    ("ta.hma", NATIVE, hma, "1"),
    ("ta.ht_trendline", NATIVE, ht_trendline, "1"),
    ("ta.hwma", NATIVE, hwma, "1"),
    ("ta.ichimoku", NATIVE, ichimoku, "1"),
    ("ta.jma", NATIVE, jma, "1"),
    ("ta.kama", NATIVE, kama, "1"),
    ("ta.linreg", NATIVE, linreg, "2"),
    ("ta.linregangle", NATIVE, linregangle, "1"),
    ("ta.linregintercept", NATIVE, linregintercept, "1"),
    ("ta.linregslope", NATIVE, linregslope, "1"),
    ("ta.ma", NATIVE, ma, "1"),
    ("ta.mama", NATIVE, mama, "1"),
    ("ta.mavp", NATIVE, mavp, "1"),
    ("ta.mcgd", NATIVE, mcgd, "1"),
    ("ta.medprice", NATIVE, medprice, "1"),
    ("ta.midpoint", NATIVE, midpoint, "1"),
    ("ta.midprice", NATIVE, midprice, "1"),
    ("ta.mmar", NATIVE, mmar, "1"),
    ("ta.ohlc4", NATIVE, ohlc4, "1"),
    ("ta.pwma", NATIVE, pwma, "1"),
    ("ta.rainbow", NATIVE, rainbow, "1"),
    ("ta.rma", NATIVE, rma, "1"),
    ("ta.sinwma", NATIVE, sinwma, "1"),
    ("ta.sma", NATIVE, sma, "1"),
    ("ta.ssf", NATIVE, ssf, "1"),
    ("ta.supertrend", NATIVE, supertrend, "1"),
    ("ta.swma", NATIVE, swma, "1"),
    ("ta.t3", NATIVE, t3, "1"),
    ("ta.tema", NATIVE, tema, "1"),
    ("ta.trima", NATIVE, trima, "1"),
    ("ta.tsf", NATIVE, tsf, "1"),
    ("ta.typprice", NATIVE, typprice, "1"),
    ("ta.vidya", NATIVE, vidya, "1"),
    ("ta.vwap", NATIVE, vwap, "1"),
    ("ta.vwma", NATIVE, vwma, "1"),
    ("ta.wcp", NATIVE, wcp, "1"),
    ("ta.wma", NATIVE, wma, "1"),
    ("ta.zlma", NATIVE, zlma, "1"),
    ("ta.drawdown", NATIVE, drawdown, "1"),
    ("ta.log_return", NATIVE, log_return, "1"),
    ("ta.percent_return", NATIVE, percent_return, "1"),
    ("ta.beta", NATIVE, beta, "1"),
    ("ta.correl", NATIVE, correl, "1"),
    ("ta.entropy", NATIVE, entropy, "1"),
    ("ta.kurtosis", NATIVE, kurtosis, "1"),
    ("ta.mad", NATIVE, mad, "1"),
    ("ta.md", NATIVE, md, "1"),
    ("ta.median", NATIVE, median, "1"),
    ("ta.quantile", NATIVE, quantile, "1"),
    ("ta.skew", NATIVE, skew, "1"),
    ("ta.stderr", NATIVE, stderr, "1"),
    ("ta.stdev", NATIVE, stdev, "1"),
    ("ta.variance", NATIVE, variance, "1"),
    ("ta.zscore", NATIVE, zscore, "1"),
    ("ta.adx", NATIVE, adx, "1"),
    ("ta.adxr", NATIVE, adxr, "1"),
    ("ta.amat", NATIVE, amat, "1"),
    ("ta.aroon", NATIVE, aroon, "1"),
    ("ta.chop", NATIVE, chop, "1"),
    ("ta.cksp", NATIVE, cksp, "1"),
    ("ta.cpr", NATIVE, cpr, "1"),
    ("ta.decay", NATIVE, decay, "1"),
    ("ta.decreasing", NATIVE, decreasing, "1"),
    ("ta.dpo", NATIVE, dpo, "1"),
    ("ta.dx", NATIVE, dx, "1"),
    ("ta.edecay", NATIVE, edecay, "1"),
    ("ta.increasing", NATIVE, increasing, "1"),
    ("ta.long_run", NATIVE, long_run, "1"),
    ("ta.minus_dm", NATIVE, minus_dm, "1"),
    ("ta.plus_dm", NATIVE, plus_dm, "1"),
    ("ta.pmax", NATIVE, pmax, "1"),
    ("ta.psar", NATIVE, psar, "1"),
    ("ta.qstick", NATIVE, qstick, "1"),
    ("ta.sarext", NATIVE, sarext, "1"),
    ("ta.short_run", NATIVE, short_run, "1"),
    ("ta.tsignals", NATIVE, tsignals, "1"),
    ("ta.ttm_trend", NATIVE, ttm_trend, "1"),
    ("ta.vhf", NATIVE, vhf, "1"),
    ("ta.vortex", NATIVE, vortex, "1"),
    ("ta.xsignals", NATIVE, xsignals, "1"),
    ("ta.aberration", NATIVE, aberration, "1"),
    ("ta.accbands", NATIVE, accbands, "1"),
    ("ta.atr", NATIVE, atr, "1"),
    ("ta.avolume", NATIVE, avolume, "1"),
    ("ta.bbands", NATIVE, bbands, "1"),
    ("ta.ce", NATIVE, ce, "1"),
    ("ta.cvi", NATIVE, cvi, "1"),
    ("ta.donchian", NATIVE, donchian, "1"),
    ("ta.hvol", NATIVE, hvol, "1"),
    ("ta.hwc", NATIVE, hwc, "1"),
    ("ta.kc", NATIVE, kc, "2"),
    ("ta.massi", NATIVE, massi, "1"),
    ("ta.natr", NATIVE, natr, "1"),
    ("ta.pdist", NATIVE, pdist, "1"),
    ("ta.rvi", NATIVE, rvi, "1"),
    ("ta.thermo", NATIVE, thermo, "1"),
    ("ta.true_range", NATIVE, true_range, "2"),
    ("ta.ui", NATIVE, ui, "1"),
    ("ta.ad", NATIVE, ad, "1"),
    ("ta.adosc", NATIVE, adosc, "1"),
    ("ta.aobv", NATIVE, aobv, "1"),
    ("ta.cmf", NATIVE, cmf, "1"),
    ("ta.efi", NATIVE, efi, "1"),
    ("ta.emv", NATIVE, emv, "1"),
    ("ta.eom", NATIVE, eom, "1"),
    ("ta.kvo", NATIVE, kvo, "1"),
    ("ta.marketfi", NATIVE, marketfi, "1"),
    ("ta.mfi", NATIVE, mfi, "1"),
    ("ta.nvi", LOCAL, nvi, "2"),
    ("ta.obv", NATIVE, obv, "1"),
    ("ta.pvi", LOCAL, pvi, "2"),
    ("ta.pvol", NATIVE, pvol, "1"),
    ("ta.pvr", NATIVE, pvr, "1"),
    ("ta.pvt", NATIVE, pvt, "1"),
    ("ta.vfi", NATIVE, vfi, "1"),
    ("ta.vosc", NATIVE, vosc, "1"),
    ("ta.wad", NATIVE, wad, "1"),
    ("ta.sma", PANDAS, sma_pandas, "1"),
)
BINDINGS = build_bindings(ENTRIES, SPECS)


def validate_backend(spec, backend):
    if backend not in (NATIVE, PANDAS, LOCAL) or backend == PANDAS and spec.id != "ta.sma":
        raise IndicatorError("backend-unavailable", spec.id, backend, backend=backend)
    # 不可用条目由运行时报告原有 unavailable-indicator，而非伪装为缺后端。
    if spec.status != "available":
        return None
    try:
        return BINDINGS[(spec.id, backend)]
    except KeyError as error:
        raise IndicatorError("backend-unavailable", spec.id, backend, backend=backend) from error


def execute(spec, inputs, parameters, backend):
    if not len(next(iter(inputs.values()))):
        return None
    binding = BINDINGS[(spec.id, backend)]
    options = dict(parameters) | dict(spec.fixed)
    if backend == NATIVE:
        options["talib"] = False
    return binding.compute(**inputs, **options)
