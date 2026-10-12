"""由 scripts/generate_indicator_api.py 生成；请修改审核目录后重新生成。"""

from __future__ import annotations

from collections.abc import Sequence

from .api import IndicatorNamespace, IndicatorResult, Inputs, Source
from .types import IndicatorHandle


class AberrationResult(IndicatorResult):
    __slots__ = ()

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def atr(self) -> IndicatorHandle:
        return self._channels["atr"]


class AccbandsResult(IndicatorResult):
    __slots__ = ()

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]


class AdxResult(IndicatorResult):
    __slots__ = ()

    @property
    def adx(self) -> IndicatorHandle:
        return self._channels["adx"]

    @property
    def positive(self) -> IndicatorHandle:
        return self._channels["positive"]

    @property
    def negative(self) -> IndicatorHandle:
        return self._channels["negative"]


class AdxrResult(IndicatorResult):
    __slots__ = ()

    @property
    def adxr(self) -> IndicatorHandle:
        return self._channels["adxr"]

    @property
    def positive(self) -> IndicatorHandle:
        return self._channels["positive"]

    @property
    def negative(self) -> IndicatorHandle:
        return self._channels["negative"]


class AlligatorResult(IndicatorResult):
    __slots__ = ()

    @property
    def jaw(self) -> IndicatorHandle:
        return self._channels["jaw"]

    @property
    def teeth(self) -> IndicatorHandle:
        return self._channels["teeth"]

    @property
    def lips(self) -> IndicatorHandle:
        return self._channels["lips"]


class AmatResult(IndicatorResult):
    __slots__ = ()

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class AnchoredVwapBandsResult(IndicatorResult):
    __slots__ = ()

    @property
    def vwap(self) -> IndicatorHandle:
        return self._channels["vwap"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]


class AobvResult(IndicatorResult):
    __slots__ = ()

    @property
    def obv(self) -> IndicatorHandle:
        return self._channels["obv"]

    @property
    def minimum(self) -> IndicatorHandle:
        return self._channels["minimum"]

    @property
    def maximum(self) -> IndicatorHandle:
        return self._channels["maximum"]

    @property
    def fast(self) -> IndicatorHandle:
        return self._channels["fast"]

    @property
    def slow(self) -> IndicatorHandle:
        return self._channels["slow"]

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class AroonResult(IndicatorResult):
    __slots__ = ()

    @property
    def down(self) -> IndicatorHandle:
        return self._channels["down"]

    @property
    def up(self) -> IndicatorHandle:
        return self._channels["up"]

    @property
    def oscillator(self) -> IndicatorHandle:
        return self._channels["oscillator"]


class AtrStopResult(IndicatorResult):
    __slots__ = ()

    @property
    def stop(self) -> IndicatorHandle:
        return self._channels["stop"]

    @property
    def direction(self) -> IndicatorHandle:
        return self._channels["direction"]


class BbandsResult(IndicatorResult):
    __slots__ = ()

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def bandwidth(self) -> IndicatorHandle:
        return self._channels["bandwidth"]

    @property
    def percent(self) -> IndicatorHandle:
        return self._channels["percent"]


class BrarResult(IndicatorResult):
    __slots__ = ()

    @property
    def ar(self) -> IndicatorHandle:
        return self._channels["ar"]

    @property
    def br(self) -> IndicatorHandle:
        return self._channels["br"]


class CdlZResult(IndicatorResult):
    __slots__ = ()

    @property
    def open(self) -> IndicatorHandle:
        return self._channels["open"]

    @property
    def high(self) -> IndicatorHandle:
        return self._channels["high"]

    @property
    def low(self) -> IndicatorHandle:
        return self._channels["low"]

    @property
    def close(self) -> IndicatorHandle:
        return self._channels["close"]


class CeResult(IndicatorResult):
    __slots__ = ()

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class CkspResult(IndicatorResult):
    __slots__ = ()

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class CprResult(IndicatorResult):
    __slots__ = ()

    @property
    def top(self) -> IndicatorHandle:
        return self._channels["top"]

    @property
    def pivot(self) -> IndicatorHandle:
        return self._channels["pivot"]

    @property
    def bottom(self) -> IndicatorHandle:
        return self._channels["bottom"]

    @property
    def r1(self) -> IndicatorHandle:
        return self._channels["r1"]

    @property
    def r2(self) -> IndicatorHandle:
        return self._channels["r2"]

    @property
    def s1(self) -> IndicatorHandle:
        return self._channels["s1"]

    @property
    def s2(self) -> IndicatorHandle:
        return self._channels["s2"]

    @property
    def width(self) -> IndicatorHandle:
        return self._channels["width"]

    @property
    def width_percent(self) -> IndicatorHandle:
        return self._channels["width_percent"]

    @property
    def width_class(self) -> IndicatorHandle:
        return self._channels["width_class"]

    @property
    def position(self) -> IndicatorHandle:
        return self._channels["position"]


class DmResult(IndicatorResult):
    __slots__ = ()

    @property
    def positive(self) -> IndicatorHandle:
        return self._channels["positive"]

    @property
    def negative(self) -> IndicatorHandle:
        return self._channels["negative"]


class DonchianResult(IndicatorResult):
    __slots__ = ()

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]


class DrawdownResult(IndicatorResult):
    __slots__ = ()

    @property
    def absolute(self) -> IndicatorHandle:
        return self._channels["absolute"]

    @property
    def percent(self) -> IndicatorHandle:
        return self._channels["percent"]

    @property
    def logarithmic(self) -> IndicatorHandle:
        return self._channels["logarithmic"]


class EriResult(IndicatorResult):
    __slots__ = ()

    @property
    def bull_power(self) -> IndicatorHandle:
        return self._channels["bull_power"]

    @property
    def bear_power(self) -> IndicatorHandle:
        return self._channels["bear_power"]


class FisherResult(IndicatorResult):
    __slots__ = ()

    @property
    def fisher(self) -> IndicatorHandle:
        return self._channels["fisher"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class GatorResult(IndicatorResult):
    __slots__ = ()

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]


class HaResult(IndicatorResult):
    __slots__ = ()

    @property
    def open(self) -> IndicatorHandle:
        return self._channels["open"]

    @property
    def high(self) -> IndicatorHandle:
        return self._channels["high"]

    @property
    def low(self) -> IndicatorHandle:
        return self._channels["low"]

    @property
    def close(self) -> IndicatorHandle:
        return self._channels["close"]


class HiloResult(IndicatorResult):
    __slots__ = ()

    @property
    def hilo(self) -> IndicatorHandle:
        return self._channels["hilo"]

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class HtPhasorResult(IndicatorResult):
    __slots__ = ()

    @property
    def inphase(self) -> IndicatorHandle:
        return self._channels["inphase"]

    @property
    def quadrature(self) -> IndicatorHandle:
        return self._channels["quadrature"]


class HtSineResult(IndicatorResult):
    __slots__ = ()

    @property
    def sine(self) -> IndicatorHandle:
        return self._channels["sine"]

    @property
    def lead_sine(self) -> IndicatorHandle:
        return self._channels["lead_sine"]


class HwcResult(IndicatorResult):
    __slots__ = ()

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]


class IchimokuResult(IndicatorResult):
    __slots__ = ()

    @property
    def span_a(self) -> IndicatorHandle:
        return self._channels["span_a"]

    @property
    def span_b(self) -> IndicatorHandle:
        return self._channels["span_b"]

    @property
    def tenkan(self) -> IndicatorHandle:
        return self._channels["tenkan"]

    @property
    def kijun(self) -> IndicatorHandle:
        return self._channels["kijun"]


class KcResult(IndicatorResult):
    __slots__ = ()

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]


class KdjResult(IndicatorResult):
    __slots__ = ()

    @property
    def k(self) -> IndicatorHandle:
        return self._channels["k"]

    @property
    def d(self) -> IndicatorHandle:
        return self._channels["d"]

    @property
    def j(self) -> IndicatorHandle:
        return self._channels["j"]


class KstResult(IndicatorResult):
    __slots__ = ()

    @property
    def kst(self) -> IndicatorHandle:
        return self._channels["kst"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class KvoResult(IndicatorResult):
    __slots__ = ()

    @property
    def kvo(self) -> IndicatorHandle:
        return self._channels["kvo"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class MaEnvelopesResult(IndicatorResult):
    __slots__ = ()

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]


class MacdResult(IndicatorResult):
    __slots__ = ()

    @property
    def macd(self) -> IndicatorHandle:
        return self._channels["macd"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]

    @property
    def line(self) -> IndicatorHandle:
        return self._channels["macd"]


class MacdextResult(IndicatorResult):
    __slots__ = ()

    @property
    def macd(self) -> IndicatorHandle:
        return self._channels["macd"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]


class MacdfixResult(IndicatorResult):
    __slots__ = ()

    @property
    def macd(self) -> IndicatorHandle:
        return self._channels["macd"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class MamaResult(IndicatorResult):
    __slots__ = ()

    @property
    def mama(self) -> IndicatorHandle:
        return self._channels["mama"]

    @property
    def fama(self) -> IndicatorHandle:
        return self._channels["fama"]


class MmarResult(IndicatorResult):
    __slots__ = ()

    @property
    def ma1(self) -> IndicatorHandle:
        return self._channels["ma1"]

    @property
    def ma2(self) -> IndicatorHandle:
        return self._channels["ma2"]

    @property
    def ma3(self) -> IndicatorHandle:
        return self._channels["ma3"]

    @property
    def ma4(self) -> IndicatorHandle:
        return self._channels["ma4"]

    @property
    def ma5(self) -> IndicatorHandle:
        return self._channels["ma5"]

    @property
    def ma6(self) -> IndicatorHandle:
        return self._channels["ma6"]


class MswResult(IndicatorResult):
    __slots__ = ()

    @property
    def sine(self) -> IndicatorHandle:
        return self._channels["sine"]

    @property
    def lead_sine(self) -> IndicatorHandle:
        return self._channels["lead_sine"]


class PivotPointsResult(IndicatorResult):
    __slots__ = ()

    @property
    def p(self) -> IndicatorHandle:
        return self._channels["p"]

    @property
    def r1(self) -> IndicatorHandle:
        return self._channels["r1"]

    @property
    def s1(self) -> IndicatorHandle:
        return self._channels["s1"]

    @property
    def r2(self) -> IndicatorHandle:
        return self._channels["r2"]

    @property
    def s2(self) -> IndicatorHandle:
        return self._channels["s2"]

    @property
    def r3(self) -> IndicatorHandle:
        return self._channels["r3"]

    @property
    def s3(self) -> IndicatorHandle:
        return self._channels["s3"]

    @property
    def r4(self) -> IndicatorHandle:
        return self._channels["r4"]

    @property
    def s4(self) -> IndicatorHandle:
        return self._channels["s4"]

    @property
    def r5(self) -> IndicatorHandle:
        return self._channels["r5"]

    @property
    def s5(self) -> IndicatorHandle:
        return self._channels["s5"]


class PivothighResult(IndicatorResult):
    __slots__ = ()

    @property
    def value(self) -> IndicatorHandle:
        return self._channels["value"]

    @property
    def pivot_bar(self) -> IndicatorHandle:
        return self._channels["pivot_bar"]

    @property
    def confirmed_at(self) -> IndicatorHandle:
        return self._channels["confirmed_at"]


class PivotlowResult(IndicatorResult):
    __slots__ = ()

    @property
    def value(self) -> IndicatorHandle:
        return self._channels["value"]

    @property
    def pivot_bar(self) -> IndicatorHandle:
        return self._channels["pivot_bar"]

    @property
    def confirmed_at(self) -> IndicatorHandle:
        return self._channels["confirmed_at"]


class PmoResult(IndicatorResult):
    __slots__ = ()

    @property
    def pmo(self) -> IndicatorHandle:
        return self._channels["pmo"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class PpoResult(IndicatorResult):
    __slots__ = ()

    @property
    def ppo(self) -> IndicatorHandle:
        return self._channels["ppo"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class PsarResult(IndicatorResult):
    __slots__ = ()

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]

    @property
    def acceleration(self) -> IndicatorHandle:
        return self._channels["acceleration"]

    @property
    def reversal(self) -> IndicatorHandle:
        return self._channels["reversal"]


class PvoResult(IndicatorResult):
    __slots__ = ()

    @property
    def pvo(self) -> IndicatorHandle:
        return self._channels["pvo"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class QqeResult(IndicatorResult):
    __slots__ = ()

    @property
    def qqe(self) -> IndicatorHandle:
        return self._channels["qqe"]

    @property
    def smoothed_rsi(self) -> IndicatorHandle:
        return self._channels["smoothed_rsi"]

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]

    @property
    def basis_long(self) -> IndicatorHandle:
        return self._channels["basis_long"]

    @property
    def basis_short(self) -> IndicatorHandle:
        return self._channels["basis_short"]

    @property
    def direction(self) -> IndicatorHandle:
        return self._channels["direction"]


class RainbowResult(IndicatorResult):
    __slots__ = ()

    @property
    def ma1(self) -> IndicatorHandle:
        return self._channels["ma1"]

    @property
    def ma2(self) -> IndicatorHandle:
        return self._channels["ma2"]

    @property
    def ma3(self) -> IndicatorHandle:
        return self._channels["ma3"]

    @property
    def ma4(self) -> IndicatorHandle:
        return self._channels["ma4"]

    @property
    def ma5(self) -> IndicatorHandle:
        return self._channels["ma5"]

    @property
    def ma6(self) -> IndicatorHandle:
        return self._channels["ma6"]

    @property
    def ma7(self) -> IndicatorHandle:
        return self._channels["ma7"]

    @property
    def ma8(self) -> IndicatorHandle:
        return self._channels["ma8"]

    @property
    def ma9(self) -> IndicatorHandle:
        return self._channels["ma9"]

    @property
    def ma10(self) -> IndicatorHandle:
        return self._channels["ma10"]


class RvgiResult(IndicatorResult):
    __slots__ = ()

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def rvgi(self) -> IndicatorHandle:
        return self._channels["rvgi"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class SmiResult(IndicatorResult):
    __slots__ = ()

    @property
    def smi(self) -> IndicatorHandle:
        return self._channels["smi"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]

    @property
    def oscillator(self) -> IndicatorHandle:
        return self._channels["oscillator"]


class SmiStochasticResult(IndicatorResult):
    __slots__ = ()

    @property
    def smi(self) -> IndicatorHandle:
        return self._channels["smi"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class SqueezeResult(IndicatorResult):
    __slots__ = ()

    @property
    def squeeze(self) -> IndicatorHandle:
        return self._channels["squeeze"]

    @property
    def on(self) -> IndicatorHandle:
        return self._channels["on"]

    @property
    def off(self) -> IndicatorHandle:
        return self._channels["off"]

    @property
    def none(self) -> IndicatorHandle:
        return self._channels["none"]


class SqueezeProResult(IndicatorResult):
    __slots__ = ()

    @property
    def squeeze(self) -> IndicatorHandle:
        return self._channels["squeeze"]

    @property
    def on_wide(self) -> IndicatorHandle:
        return self._channels["on_wide"]

    @property
    def on_normal(self) -> IndicatorHandle:
        return self._channels["on_normal"]

    @property
    def on_narrow(self) -> IndicatorHandle:
        return self._channels["on_narrow"]

    @property
    def off(self) -> IndicatorHandle:
        return self._channels["off"]

    @property
    def none(self) -> IndicatorHandle:
        return self._channels["none"]


class StarcResult(IndicatorResult):
    __slots__ = ()

    @property
    def middle(self) -> IndicatorHandle:
        return self._channels["middle"]

    @property
    def upper(self) -> IndicatorHandle:
        return self._channels["upper"]

    @property
    def lower(self) -> IndicatorHandle:
        return self._channels["lower"]


class StcResult(IndicatorResult):
    __slots__ = ()

    @property
    def stc(self) -> IndicatorHandle:
        return self._channels["stc"]

    @property
    def macd(self) -> IndicatorHandle:
        return self._channels["macd"]

    @property
    def stochastic(self) -> IndicatorHandle:
        return self._channels["stochastic"]


class StochResult(IndicatorResult):
    __slots__ = ()

    @property
    def k(self) -> IndicatorHandle:
        return self._channels["k"]

    @property
    def d(self) -> IndicatorHandle:
        return self._channels["d"]


class StochfResult(IndicatorResult):
    __slots__ = ()

    @property
    def k(self) -> IndicatorHandle:
        return self._channels["k"]

    @property
    def d(self) -> IndicatorHandle:
        return self._channels["d"]


class StochrsiResult(IndicatorResult):
    __slots__ = ()

    @property
    def k(self) -> IndicatorHandle:
        return self._channels["k"]

    @property
    def d(self) -> IndicatorHandle:
        return self._channels["d"]


class SupertrendResult(IndicatorResult):
    __slots__ = ()

    @property
    def trend(self) -> IndicatorHandle:
        return self._channels["trend"]

    @property
    def direction(self) -> IndicatorHandle:
        return self._channels["direction"]

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class TdSeqResult(IndicatorResult):
    __slots__ = ()

    @property
    def up(self) -> IndicatorHandle:
        return self._channels["up"]

    @property
    def down(self) -> IndicatorHandle:
        return self._channels["down"]


class ThermoResult(IndicatorResult):
    __slots__ = ()

    @property
    def thermo(self) -> IndicatorHandle:
        return self._channels["thermo"]

    @property
    def average(self) -> IndicatorHandle:
        return self._channels["average"]

    @property
    def long(self) -> IndicatorHandle:
        return self._channels["long"]

    @property
    def short(self) -> IndicatorHandle:
        return self._channels["short"]


class TrixResult(IndicatorResult):
    __slots__ = ()

    @property
    def trix(self) -> IndicatorHandle:
        return self._channels["trix"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class TrixhResult(IndicatorResult):
    __slots__ = ()

    @property
    def trix(self) -> IndicatorHandle:
        return self._channels["trix"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]


class TsiResult(IndicatorResult):
    __slots__ = ()

    @property
    def tsi(self) -> IndicatorHandle:
        return self._channels["tsi"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class TsignalsResult(IndicatorResult):
    __slots__ = ()

    @property
    def trend(self) -> IndicatorHandle:
        return self._channels["trend"]

    @property
    def trades(self) -> IndicatorHandle:
        return self._channels["trades"]

    @property
    def entries(self) -> IndicatorHandle:
        return self._channels["entries"]

    @property
    def exits(self) -> IndicatorHandle:
        return self._channels["exits"]


class VolatilityStopResult(IndicatorResult):
    __slots__ = ()

    @property
    def stop(self) -> IndicatorHandle:
        return self._channels["stop"]

    @property
    def direction(self) -> IndicatorHandle:
        return self._channels["direction"]


class VortexResult(IndicatorResult):
    __slots__ = ()

    @property
    def positive(self) -> IndicatorHandle:
        return self._channels["positive"]

    @property
    def negative(self) -> IndicatorHandle:
        return self._channels["negative"]


class VwmacdResult(IndicatorResult):
    __slots__ = ()

    @property
    def macd(self) -> IndicatorHandle:
        return self._channels["macd"]

    @property
    def histogram(self) -> IndicatorHandle:
        return self._channels["histogram"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class WavetrendResult(IndicatorResult):
    __slots__ = ()

    @property
    def wave(self) -> IndicatorHandle:
        return self._channels["wave"]

    @property
    def signal(self) -> IndicatorHandle:
        return self._channels["signal"]


class XsignalsResult(IndicatorResult):
    __slots__ = ()

    @property
    def trend(self) -> IndicatorHandle:
        return self._channels["trend"]

    @property
    def trades(self) -> IndicatorHandle:
        return self._channels["trades"]

    @property
    def entries(self) -> IndicatorHandle:
        return self._channels["entries"]

    @property
    def exits(self) -> IndicatorHandle:
        return self._channels["exits"]


class TechnicalAnalysis(IndicatorNamespace):
    """当前策略的技术分析入口；序列指标在 init() 登记，is_* 即时判断可在 next() 调用。"""

    def aberration(
        self,
        *,
        length: int = 5,
        atr_length: int = 15,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AberrationResult:
        """ta.aberration；输入：high, low, close；输出：middle, upper, lower, atr。参数按审核目录校验。"""
        return AberrationResult(
            self._call(
                "ta.aberration",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "atr_length": atr_length},
            )
        )

    def ac(
        self,
        *,
        fast: int = 5,
        slow: int = 34,
        signal: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ac；输入：high, low；输出：ac。参数按审核目录校验。"""
        return self._call(
            "ta.ac",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"fast": fast, "slow": slow, "signal": signal},
        )

    def accbands(
        self,
        *,
        length: int = 20,
        c: int = 4,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AccbandsResult:
        """ta.accbands；输入：high, low, close；输出：lower, middle, upper。参数按审核目录校验。"""
        return AccbandsResult(
            self._call(
                "ta.accbands",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "c": c, "mamode": mamode},
            )
        )

    def ad(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ad；输入：high, low, close, volume；输出：ad。参数按审核目录校验。"""
        return self._call("ta.ad", "", None, inputs, backend, required_outputs, {})

    def adosc(
        self,
        *,
        fast: int = 3,
        slow: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.adosc；输入：high, low, close, volume；输出：adosc。参数按审核目录校验。"""
        return self._call(
            "ta.adosc", "", None, inputs, backend, required_outputs, {"fast": fast, "slow": slow}
        )

    def adr(
        self,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.adr；输入：high, low；输出：adr。参数按审核目录校验。"""
        return self._call("ta.adr", "", None, inputs, backend, required_outputs, {"length": length})

    def adx(
        self,
        *,
        length: int = 14,
        lensig: int = 14,
        scalar: int = 100,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AdxResult:
        """ta.adx；输入：high, low, close；输出：adx, positive, negative。参数按审核目录校验。"""
        return AdxResult(
            self._call(
                "ta.adx",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "length": length,
                    "lensig": lensig,
                    "scalar": scalar,
                    "mamode": mamode,
                    "drift": drift,
                },
            )
        )

    def adxr(
        self,
        *,
        length: int = 14,
        lensig: int = 14,
        scalar: float = 100.0,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AdxrResult:
        """ta.adxr；输入：high, low, close；输出：adxr, positive, negative。参数按审核目录校验。"""
        return AdxrResult(
            self._call(
                "ta.adxr",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "length": length,
                    "lensig": lensig,
                    "scalar": scalar,
                    "mamode": mamode,
                    "drift": drift,
                },
            )
        )

    def alligator(
        self,
        *,
        jaw: int = 13,
        teeth: int = 8,
        lips: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AlligatorResult:
        """ta.alligator；输入：high, low；输出：jaw, teeth, lips。参数按审核目录校验。"""
        return AlligatorResult(
            self._call(
                "ta.alligator",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"jaw": jaw, "teeth": teeth, "lips": lips},
            )
        )

    def alma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        sigma: float = 6.0,
        distribution_offset: float = 0.85,
        floor: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.alma；输入：close；输出：alma。参数按审核目录校验。"""
        return self._call(
            "ta.alma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {
                "length": length,
                "sigma": sigma,
                "distribution_offset": distribution_offset,
                "floor": floor,
            },
        )

    def amat(
        self,
        source: Source | None = None,
        *,
        fast: int = 8,
        slow: int = 21,
        lookback: int = 2,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AmatResult:
        """ta.amat；输入：close；输出：long, short。参数按审核目录校验。"""
        return AmatResult(
            self._call(
                "ta.amat",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "lookback": lookback, "mamode": mamode},
            )
        )

    def anchored_vwap(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.anchored_vwap；输入：source, volume, anchor；输出：vwap。参数按审核目录校验。"""
        return self._call("ta.anchored_vwap", "", None, inputs, backend, required_outputs, {})

    def anchored_vwap_bands(
        self,
        *,
        stdev_mult: float = 1.0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AnchoredVwapBandsResult:
        """ta.anchored_vwap_bands；输入：source, volume, anchor；输出：vwap, lower, upper。参数按审核目录校验。"""
        return AnchoredVwapBandsResult(
            self._call(
                "ta.anchored_vwap_bands",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"stdev_mult": stdev_mult},
            )
        )

    def ao(
        self,
        *,
        fast: int = 5,
        slow: int = 34,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ao；输入：high, low；输出：ao。参数按审核目录校验。"""
        return self._call(
            "ta.ao", "", None, inputs, backend, required_outputs, {"fast": fast, "slow": slow}
        )

    def aobv(
        self,
        *,
        fast: int = 4,
        slow: int = 12,
        max_lookback: int = 2,
        min_lookback: int = 2,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AobvResult:
        """ta.aobv；输入：close, volume；输出：obv, minimum, maximum, fast, slow, long, short。参数按审核目录校验。"""
        return AobvResult(
            self._call(
                "ta.aobv",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "fast": fast,
                    "slow": slow,
                    "max_lookback": max_lookback,
                    "min_lookback": min_lookback,
                    "mamode": mamode,
                },
            )
        )

    def apo(
        self,
        source: Source | None = None,
        *,
        fast: int = 12,
        slow: int = 26,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.apo；输入：close；输出：apo。参数按审核目录校验。"""
        return self._call(
            "ta.apo",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"fast": fast, "slow": slow, "mamode": mamode},
        )

    def aroon(
        self,
        *,
        length: int = 14,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AroonResult:
        """ta.aroon；输入：high, low；输出：down, up, oscillator。参数按审核目录校验。"""
        return AroonResult(
            self._call(
                "ta.aroon",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "scalar": scalar},
            )
        )

    def atr(
        self,
        *,
        length: int = 14,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.atr；输入：high, low, close；输出：atr。参数按审核目录校验。"""
        return self._call(
            "ta.atr",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "mamode": mamode, "drift": drift},
        )

    def atr_stop(
        self,
        *,
        length: int = 21,
        multiplier: float = 3,
        end_type: str = "close",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> AtrStopResult:
        """ta.atr_stop；输入：high, low, close；输出：stop, direction。参数按审核目录校验。"""
        return AtrStopResult(
            self._call(
                "ta.atr_stop",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "multiplier": multiplier, "end_type": end_type},
            )
        )

    def avgprice(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.avgprice；输入：open_, high, low, close；输出：avgprice。参数按审核目录校验。"""
        return self._call("ta.avgprice", "", None, inputs, backend, required_outputs, {})

    def avolume(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.avolume；输入：close；输出：avolume。参数按审核目录校验。"""
        return self._call(
            "ta.avolume", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def barssince(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.barssince；输入：condition；输出：barssince。参数按审核目录校验。"""
        return self._call(
            "ta.barssince", "condition", source, inputs, backend, required_outputs, {}
        )

    def bbands(
        self,
        source: Source | None = None,
        *,
        length: int = 5,
        std: float = 2.0,
        ddof: int = 0,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> BbandsResult:
        """ta.bbands；输入：close；输出：lower, middle, upper, bandwidth, percent。参数按审核目录校验。"""
        return BbandsResult(
            self._call(
                "ta.bbands",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "std": std, "ddof": ddof, "mamode": mamode},
            )
        )

    def beta(
        self,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.beta；输入：close, benchmark；输出：beta。参数按审核目录校验。"""
        return self._call(
            "ta.beta", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def bias(
        self,
        source: Source | None = None,
        *,
        length: int = 26,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.bias；输入：close；输出：bias。参数按审核目录校验。"""
        return self._call(
            "ta.bias",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "mamode": mamode},
        )

    def bop(
        self,
        *,
        scalar: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.bop；输入：open_, high, low, close；输出：bop。参数按审核目录校验。"""
        return self._call("ta.bop", "", None, inputs, backend, required_outputs, {"scalar": scalar})

    def brar(
        self,
        *,
        length: int = 26,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> BrarResult:
        """ta.brar；输入：open_, high, low, close；输出：ar, br。参数按审核目录校验。"""
        return BrarResult(
            self._call(
                "ta.brar",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "scalar": scalar, "drift": drift},
            )
        )

    def cci(
        self,
        *,
        length: int = 14,
        c: float = 0.015,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cci；输入：high, low, close；输出：cci。参数按审核目录校验。"""
        return self._call(
            "ta.cci", "", None, inputs, backend, required_outputs, {"length": length, "c": c}
        )

    def cdl_doji(
        self,
        *,
        length: int = 10,
        factor: float = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_doji；输入：open_, high, low, close；输出：cdl_doji。参数按审核目录校验。"""
        return self._call(
            "ta.cdl_doji",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "factor": factor},
        )

    def cdl_engulfing(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_engulfing；输入：open_, high, low, close；输出：cdl_engulfing。参数按审核目录校验。"""
        return self._call("ta.cdl_engulfing", "", None, inputs, backend, required_outputs, {})

    def cdl_eveningstar(
        self,
        *,
        penetration: float = 0.3,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_eveningstar；输入：open_, high, low, close；输出：cdl_eveningstar。参数按审核目录校验。"""
        return self._call(
            "ta.cdl_eveningstar",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"penetration": penetration},
        )

    def cdl_hammer(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_hammer；输入：open_, high, low, close；输出：cdl_hammer。参数按审核目录校验。"""
        return self._call("ta.cdl_hammer", "", None, inputs, backend, required_outputs, {})

    def cdl_harami(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_harami；输入：open_, high, low, close；输出：cdl_harami。参数按审核目录校验。"""
        return self._call("ta.cdl_harami", "", None, inputs, backend, required_outputs, {})

    def cdl_inside(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_inside；输入：open_, high, low, close；输出：cdl_inside。参数按审核目录校验。"""
        return self._call("ta.cdl_inside", "", None, inputs, backend, required_outputs, {})

    def cdl_marubozu(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_marubozu；输入：open_, high, low, close；输出：cdl_marubozu。参数按审核目录校验。"""
        return self._call("ta.cdl_marubozu", "", None, inputs, backend, required_outputs, {})

    def cdl_morningstar(
        self,
        *,
        penetration: float = 0.3,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_morningstar；输入：open_, high, low, close；输出：cdl_morningstar。参数按审核目录校验。"""
        return self._call(
            "ta.cdl_morningstar",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"penetration": penetration},
        )

    def cdl_shootingstar(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cdl_shootingstar；输入：open_, high, low, close；输出：cdl_shootingstar。参数按审核目录校验。"""
        return self._call("ta.cdl_shootingstar", "", None, inputs, backend, required_outputs, {})

    def cdl_z(
        self,
        *,
        length: int = 30,
        ddof: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> CdlZResult:
        """ta.cdl_z；输入：open_, high, low, close；输出：open, high, low, close。参数按审核目录校验。"""
        return CdlZResult(
            self._call(
                "ta.cdl_z",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "ddof": ddof},
            )
        )

    def ce(
        self,
        *,
        length: int = 22,
        multiplier: float = 3.0,
        mamode: str = "rma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> CeResult:
        """ta.ce；输入：high, low, close；输出：long, short。参数按审核目录校验。"""
        return CeResult(
            self._call(
                "ta.ce",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "multiplier": multiplier, "mamode": mamode},
            )
        )

    def cfo(
        self,
        source: Source | None = None,
        *,
        length: int = 9,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cfo；输入：close；输出：cfo。参数按审核目录校验。"""
        return self._call(
            "ta.cfo",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar},
        )

    def cg(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cg；输入：close；输出：cg。参数按审核目录校验。"""
        return self._call(
            "ta.cg", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def change(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.change；输入：source；输出：change。参数按审核目录校验。"""
        return self._call(
            "ta.change", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def chop(
        self,
        *,
        length: int = 14,
        atr_length: int = 1,
        ln: bool = False,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.chop；输入：high, low, close；输出：chop。参数按审核目录校验。"""
        return self._call(
            "ta.chop",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "atr_length": atr_length, "ln": ln, "scalar": scalar},
        )

    def cksp(
        self,
        *,
        p: int = 10,
        x: int = 3,
        q: int = 20,
        tvmode: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> CkspResult:
        """ta.cksp；输入：high, low, close；输出：long, short。参数按审核目录校验。"""
        return CkspResult(
            self._call(
                "ta.cksp",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"p": p, "x": x, "q": q, "tvmode": tvmode},
            )
        )

    def cmf(
        self,
        *,
        length: int = 20,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cmf；输入：high, low, close, volume；输出：cmf。参数按审核目录校验。"""
        return self._call("ta.cmf", "", None, inputs, backend, required_outputs, {"length": length})

    def cmo(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cmo；输入：close；输出：cmo。参数按审核目录校验。"""
        return self._call(
            "ta.cmo",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar, "drift": drift},
        )

    def coppock(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        fast: int = 11,
        slow: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.coppock；输入：close；输出：coppock。参数按审核目录校验。"""
        return self._call(
            "ta.coppock",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "fast": fast, "slow": slow},
        )

    def correl(
        self,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.correl；输入：close, benchmark；输出：correl。参数按审核目录校验。"""
        return self._call(
            "ta.correl", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def cpr(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> CprResult:
        """ta.cpr；输入：open_, high, low, close, volume；输出：top, pivot, bottom, r1, r2, s1, s2, width, width_percent, width_class, position。参数按审核目录校验。"""
        return CprResult(self._call("ta.cpr", "", None, inputs, backend, required_outputs, {}))

    def cross(
        self,
        left: Source | None = None,
        right: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cross；输入：left, right；输出：cross。参数按审核目录校验。"""
        return self._call_inputs(
            "ta.cross", {"left": left, "right": right}, inputs, backend, required_outputs, {}
        )

    def crossover(
        self,
        left: Source | None = None,
        right: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.crossover；输入：left, right；输出：crossover。参数按审核目录校验。"""
        return self._call_inputs(
            "ta.crossover", {"left": left, "right": right}, inputs, backend, required_outputs, {}
        )

    def crossunder(
        self,
        left: Source | None = None,
        right: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.crossunder；输入：left, right；输出：crossunder。参数按审核目录校验。"""
        return self._call_inputs(
            "ta.crossunder", {"left": left, "right": right}, inputs, backend, required_outputs, {}
        )

    def crsi(
        self,
        source: Source | None = None,
        *,
        length: int = 3,
        streak: int = 2,
        rank: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.crsi；输入：close；输出：crsi。参数按审核目录校验。"""
        return self._call(
            "ta.crsi",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "streak": streak, "rank": rank},
        )

    def cti(
        self,
        source: Source | None = None,
        *,
        length: int = 12,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cti；输入：close；输出：cti。参数按审核目录校验。"""
        return self._call(
            "ta.cti", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def cum(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cum；输入：source；输出：cum。参数按审核目录校验。"""
        return self._call("ta.cum", "source", source, inputs, backend, required_outputs, {})

    def cvi(
        self,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.cvi；输入：high, low；输出：cvi。参数按审核目录校验。"""
        return self._call("ta.cvi", "", None, inputs, backend, required_outputs, {"length": length})

    def decay(
        self,
        source: Source | None = None,
        *,
        length: int = 5,
        mode: str = "linear",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.decay；输入：close；输出：decay。参数按审核目录校验。"""
        return self._call(
            "ta.decay",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "mode": mode},
        )

    def decreasing(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        strict: bool = False,
        asint: bool = True,
        percent: bool = False,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.decreasing；输入：close；输出：decreasing。参数按审核目录校验。"""
        return self._call(
            "ta.decreasing",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {
                "length": length,
                "strict": strict,
                "asint": asint,
                "percent": percent,
                "drift": drift,
            },
        )

    def dema(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.dema；输入：close；输出：dema。参数按审核目录校验。"""
        return self._call(
            "ta.dema", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def dm(
        self,
        *,
        length: int = 14,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> DmResult:
        """ta.dm；输入：high, low；输出：positive, negative。参数按审核目录校验。"""
        return DmResult(
            self._call(
                "ta.dm",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "mamode": mamode, "drift": drift},
            )
        )

    def donchian(
        self,
        *,
        lower_length: int = 20,
        upper_length: int = 20,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> DonchianResult:
        """ta.donchian；输入：high, low；输出：lower, middle, upper。参数按审核目录校验。"""
        return DonchianResult(
            self._call(
                "ta.donchian",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"lower_length": lower_length, "upper_length": upper_length},
            )
        )

    def dpo(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.dpo；输入：close；输出：dpo。参数按审核目录校验。"""
        return self._call(
            "ta.dpo", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def drawdown(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> DrawdownResult:
        """ta.drawdown；输入：close；输出：absolute, percent, logarithmic。参数按审核目录校验。"""
        return DrawdownResult(
            self._call("ta.drawdown", "close", source, inputs, backend, required_outputs, {})
        )

    def dsp(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.dsp；输入：close；输出：dsp。参数按审核目录校验。"""
        return self._call(
            "ta.dsp", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def dx(
        self,
        *,
        length: int = 14,
        scalar: int = 100,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.dx；输入：high, low, close；输出：dx。参数按审核目录校验。"""
        return self._call(
            "ta.dx",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar, "mamode": mamode, "drift": drift},
        )

    def ebsw(
        self,
        source: Source | None = None,
        *,
        length: int = 40,
        bars: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ebsw；输入：close；输出：ebsw。参数按审核目录校验。"""
        return self._call(
            "ta.ebsw",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "bars": bars},
        )

    def edecay(
        self,
        source: Source | None = None,
        *,
        length: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.edecay；输入：close；输出：edecay。参数按审核目录校验。"""
        return self._call(
            "ta.edecay", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def efi(
        self,
        *,
        length: int = 13,
        mamode: str = "ema",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.efi；输入：close, volume；输出：efi。参数按审核目录校验。"""
        return self._call(
            "ta.efi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "mamode": mamode, "drift": drift},
        )

    def ema(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        adjust: bool = False,
        sma: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ema；输入：close；输出：ema。参数按审核目录校验。"""
        return self._call(
            "ta.ema",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "adjust": adjust, "sma": sma},
        )

    def emv(
        self,
        *,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.emv；输入：high, low, volume；输出：emv。参数按审核目录校验。"""
        return self._call("ta.emv", "", None, inputs, backend, required_outputs, {"drift": drift})

    def entropy(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        base: float = 2.0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.entropy；输入：close；输出：entropy。参数按审核目录校验。"""
        return self._call(
            "ta.entropy",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "base": base},
        )

    def eom(
        self,
        *,
        length: int = 14,
        divisor: int = 100000000,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.eom；输入：high, low, close, volume；输出：eom。参数按审核目录校验。"""
        return self._call(
            "ta.eom",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "divisor": divisor, "drift": drift},
        )

    def er(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.er；输入：close；输出：er。参数按审核目录校验。"""
        return self._call(
            "ta.er",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def eri(
        self,
        *,
        length: int = 13,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> EriResult:
        """ta.eri；输入：high, low, close；输出：bull_power, bear_power。参数按审核目录校验。"""
        return EriResult(
            self._call("ta.eri", "", None, inputs, backend, required_outputs, {"length": length})
        )

    def falling(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.falling；输入：source；输出：falling。参数按审核目录校验。"""
        return self._call(
            "ta.falling", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def fisher(
        self,
        *,
        length: int = 9,
        signal: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> FisherResult:
        """ta.fisher；输入：high, low；输出：fisher, signal。参数按审核目录校验。"""
        return FisherResult(
            self._call(
                "ta.fisher",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "signal": signal},
            )
        )

    def fosc(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.fosc；输入：close；输出：fosc。参数按审核目录校验。"""
        return self._call(
            "ta.fosc", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def frama(
        self,
        *,
        length: int = 16,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.frama；输入：high, low, close；输出：frama。参数按审核目录校验。"""
        return self._call(
            "ta.frama", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def fwma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        asc: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.fwma；输入：close；输出：fwma。参数按审核目录校验。"""
        return self._call(
            "ta.fwma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "asc": asc},
        )

    def gator(
        self,
        *,
        jaw: int = 13,
        teeth: int = 8,
        lips: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> GatorResult:
        """ta.gator；输入：high, low；输出：upper, lower。参数按审核目录校验。"""
        return GatorResult(
            self._call(
                "ta.gator",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"jaw": jaw, "teeth": teeth, "lips": lips},
            )
        )

    def ha(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> HaResult:
        """ta.ha；输入：open_, high, low, close；输出：open, high, low, close。参数按审核目录校验。"""
        return HaResult(self._call("ta.ha", "", None, inputs, backend, required_outputs, {}))

    def highest(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.highest；输入：source；输出：highest。参数按审核目录校验。"""
        return self._call(
            "ta.highest", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def highestbars(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.highestbars；输入：source；输出：highestbars。参数按审核目录校验。"""
        return self._call(
            "ta.highestbars",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length},
        )

    def hilo(
        self,
        *,
        high_length: int = 13,
        low_length: int = 21,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> HiloResult:
        """ta.hilo；输入：high, low, close；输出：hilo, long, short。参数按审核目录校验。"""
        return HiloResult(
            self._call(
                "ta.hilo",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"high_length": high_length, "low_length": low_length, "mamode": mamode},
            )
        )

    def hl2(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.hl2；输入：high, low；输出：hl2。参数按审核目录校验。"""
        return self._call("ta.hl2", "", None, inputs, backend, required_outputs, {})

    def hlc3(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.hlc3；输入：high, low, close；输出：hlc3。参数按审核目录校验。"""
        return self._call("ta.hlc3", "", None, inputs, backend, required_outputs, {})

    def hma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.hma；输入：close；输出：hma。参数按审核目录校验。"""
        return self._call(
            "ta.hma", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def ht_dcperiod(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ht_dcperiod；输入：close；输出：ht_dcperiod。参数按审核目录校验。"""
        return self._call("ta.ht_dcperiod", "close", source, inputs, backend, required_outputs, {})

    def ht_dcphase(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ht_dcphase；输入：close；输出：ht_dcphase。参数按审核目录校验。"""
        return self._call("ta.ht_dcphase", "close", source, inputs, backend, required_outputs, {})

    def ht_phasor(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> HtPhasorResult:
        """ta.ht_phasor；输入：close；输出：inphase, quadrature。参数按审核目录校验。"""
        return HtPhasorResult(
            self._call("ta.ht_phasor", "close", source, inputs, backend, required_outputs, {})
        )

    def ht_sine(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> HtSineResult:
        """ta.ht_sine；输入：close；输出：sine, lead_sine。参数按审核目录校验。"""
        return HtSineResult(
            self._call("ta.ht_sine", "close", source, inputs, backend, required_outputs, {})
        )

    def ht_trendline(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ht_trendline；输入：close；输出：ht_trendline。参数按审核目录校验。"""
        return self._call("ta.ht_trendline", "close", source, inputs, backend, required_outputs, {})

    def ht_trendmode(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ht_trendmode；输入：close；输出：ht_trendmode。参数按审核目录校验。"""
        return self._call("ta.ht_trendmode", "close", source, inputs, backend, required_outputs, {})

    def hvol(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        annualization: int = 252,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.hvol；输入：close；输出：hvol。参数按审核目录校验。"""
        return self._call(
            "ta.hvol",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "annualization": annualization},
        )

    def hwc(
        self,
        source: Source | None = None,
        *,
        na: float = 0.2,
        nb: float = 0.1,
        nc: float = 0.1,
        nd: float = 0.1,
        scalar: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> HwcResult:
        """ta.hwc；输入：close；输出：middle, upper, lower。参数按审核目录校验。"""
        return HwcResult(
            self._call(
                "ta.hwc",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"na": na, "nb": nb, "nc": nc, "nd": nd, "scalar": scalar},
            )
        )

    def hwma(
        self,
        source: Source | None = None,
        *,
        na: float = 0.2,
        nb: float = 0.1,
        nc: float = 0.1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.hwma；输入：close；输出：hwma。参数按审核目录校验。"""
        return self._call(
            "ta.hwma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"na": na, "nb": nb, "nc": nc},
        )

    def ibs(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ibs；输入：high, low, close；输出：ibs。参数按审核目录校验。"""
        return self._call("ta.ibs", "", None, inputs, backend, required_outputs, {})

    def ichimoku(
        self,
        *,
        tenkan: int = 9,
        kijun: int = 26,
        senkou: int = 52,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IchimokuResult:
        """ta.ichimoku；输入：high, low, close；输出：span_a, span_b, tenkan, kijun。参数按审核目录校验。"""
        return IchimokuResult(
            self._call(
                "ta.ichimoku",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"tenkan": tenkan, "kijun": kijun, "senkou": senkou},
            )
        )

    def iii(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.iii；输入：high, low, close, volume；输出：iii。参数按审核目录校验。"""
        return self._call("ta.iii", "", None, inputs, backend, required_outputs, {})

    def increasing(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        strict: bool = False,
        asint: bool = True,
        percent: bool = False,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.increasing；输入：close；输出：increasing。参数按审核目录校验。"""
        return self._call(
            "ta.increasing",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {
                "length": length,
                "strict": strict,
                "asint": asint,
                "percent": percent,
                "drift": drift,
            },
        )

    def inertia(
        self,
        *,
        length: int = 20,
        rvi_length: int = 14,
        scalar: int = 100,
        refined: bool = False,
        thirds: bool = False,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.inertia；输入：close, high, low；输出：inertia。参数按审核目录校验。"""
        return self._call(
            "ta.inertia",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {
                "length": length,
                "rvi_length": rvi_length,
                "scalar": scalar,
                "refined": refined,
                "thirds": thirds,
                "mamode": mamode,
            },
        )

    def jma(
        self,
        source: Source | None = None,
        *,
        length: int = 7,
        phase: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.jma；输入：close；输出：jma。参数按审核目录校验。"""
        return self._call(
            "ta.jma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "phase": phase},
        )

    def kama(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        fast: int = 2,
        slow: int = 30,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.kama；输入：close；输出：kama。参数按审核目录校验。"""
        return self._call(
            "ta.kama",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "fast": fast, "slow": slow, "drift": drift},
        )

    def kc(
        self,
        *,
        length: int = 20,
        scalar: int = 2,
        mamode: str = "ema",
        use_true_range: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> KcResult:
        """ta.kc；输入：high, low, close；输出：lower, middle, upper。参数按审核目录校验。"""
        return KcResult(
            self._call(
                "ta.kc",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "length": length,
                    "scalar": scalar,
                    "mamode": mamode,
                    "use_true_range": use_true_range,
                },
            )
        )

    def kdj(
        self,
        *,
        length: int = 9,
        signal: int = 3,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> KdjResult:
        """ta.kdj；输入：high, low, close；输出：k, d, j。参数按审核目录校验。"""
        return KdjResult(
            self._call(
                "ta.kdj",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "signal": signal},
            )
        )

    def kst(
        self,
        source: Source | None = None,
        *,
        roc1: int = 10,
        roc2: int = 15,
        roc3: int = 20,
        roc4: int = 30,
        sma1: int = 10,
        sma2: int = 10,
        sma3: int = 10,
        sma4: int = 15,
        signal: int = 9,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> KstResult:
        """ta.kst；输入：close；输出：kst, signal。参数按审核目录校验。"""
        return KstResult(
            self._call(
                "ta.kst",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {
                    "roc1": roc1,
                    "roc2": roc2,
                    "roc3": roc3,
                    "roc4": roc4,
                    "sma1": sma1,
                    "sma2": sma2,
                    "sma3": sma3,
                    "sma4": sma4,
                    "signal": signal,
                },
            )
        )

    def kurtosis(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.kurtosis；输入：close；输出：kurtosis。参数按审核目录校验。"""
        return self._call(
            "ta.kurtosis", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def kvo(
        self,
        *,
        fast: int = 34,
        slow: int = 55,
        signal: int = 13,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> KvoResult:
        """ta.kvo；输入：high, low, close, volume；输出：kvo, signal。参数按审核目录校验。"""
        return KvoResult(
            self._call(
                "ta.kvo",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal, "mamode": mamode},
            )
        )

    def linreg(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        offset: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.linreg；输入：close；输出：linreg。参数按审核目录校验。"""
        return self._call(
            "ta.linreg",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "offset": offset},
        )

    def linregangle(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.linregangle；输入：close；输出：linregangle。参数按审核目录校验。"""
        return self._call(
            "ta.linregangle", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def linregintercept(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.linregintercept；输入：close；输出：linregintercept。参数按审核目录校验。"""
        return self._call(
            "ta.linregintercept",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length},
        )

    def linregslope(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.linregslope；输入：close；输出：linregslope。参数按审核目录校验。"""
        return self._call(
            "ta.linregslope", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def log_return(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        cumulative: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.log_return；输入：close；输出：log_return。参数按审核目录校验。"""
        return self._call(
            "ta.log_return",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "cumulative": cumulative},
        )

    def long_run(
        self,
        *,
        length: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.long_run；输入：fast, slow；输出：long_run。参数按审核目录校验。"""
        return self._call(
            "ta.long_run", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def lowest(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.lowest；输入：source；输出：lowest。参数按审核目录校验。"""
        return self._call(
            "ta.lowest", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def lowestbars(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.lowestbars；输入：source；输出：lowestbars。参数按审核目录校验。"""
        return self._call(
            "ta.lowestbars", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def lrsi(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        gamma: float = 0.5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.lrsi；输入：close；输出：lrsi。参数按审核目录校验。"""
        return self._call(
            "ta.lrsi",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "gamma": gamma},
        )

    def ma(
        self,
        source: Source | None = None,
        *,
        name: str = "sma",
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ma；输入：source；输出：ma。参数按审核目录校验。"""
        return self._call(
            "ta.ma",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"name": name, "length": length},
        )

    def ma_envelopes(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        percent: float = 2.5,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MaEnvelopesResult:
        """ta.ma_envelopes；输入：close；输出：middle, upper, lower。参数按审核目录校验。"""
        return MaEnvelopesResult(
            self._call(
                "ta.ma_envelopes",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "percent": percent, "mamode": mamode},
            )
        )

    def macd(
        self,
        source: Source | None = None,
        *,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MacdResult:
        """ta.macd；输入：close；输出：macd, histogram, signal。参数按审核目录校验。"""
        return MacdResult(
            self._call(
                "ta.macd",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal},
            )
        )

    def macdext(
        self,
        source: Source | None = None,
        *,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        fastmatype: int = 1,
        slowmatype: int = 1,
        signalmatype: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MacdextResult:
        """ta.macdext；输入：close；输出：macd, signal, histogram。参数按审核目录校验。"""
        return MacdextResult(
            self._call(
                "ta.macdext",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "fastmatype": fastmatype,
                    "slowmatype": slowmatype,
                    "signalmatype": signalmatype,
                },
            )
        )

    def macdfix(
        self,
        source: Source | None = None,
        *,
        signal: int = 9,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MacdfixResult:
        """ta.macdfix；输入：close；输出：macd, histogram, signal。参数按审核目录校验。"""
        return MacdfixResult(
            self._call(
                "ta.macdfix", "close", source, inputs, backend, required_outputs, {"signal": signal}
            )
        )

    def mad(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mad；输入：close；输出：mad。参数按审核目录校验。"""
        return self._call(
            "ta.mad", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def mama(
        self,
        source: Source | None = None,
        *,
        fastlimit: float = 0.5,
        slowlimit: float = 0.05,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MamaResult:
        """ta.mama；输入：close；输出：mama, fama。参数按审核目录校验。"""
        return MamaResult(
            self._call(
                "ta.mama",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"fastlimit": fastlimit, "slowlimit": slowlimit},
            )
        )

    def marketfi(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.marketfi；输入：high, low, volume；输出：marketfi。参数按审核目录校验。"""
        return self._call("ta.marketfi", "", None, inputs, backend, required_outputs, {})

    def massi(
        self,
        *,
        fast: int = 9,
        slow: int = 25,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.massi；输入：high, low；输出：massi。参数按审核目录校验。"""
        return self._call(
            "ta.massi", "", None, inputs, backend, required_outputs, {"fast": fast, "slow": slow}
        )

    def mavp(
        self,
        *,
        minperiod: int = 2,
        maxperiod: int = 30,
        mamode: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mavp；输入：close, periods；输出：mavp。参数按审核目录校验。"""
        return self._call(
            "ta.mavp",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"minperiod": minperiod, "maxperiod": maxperiod, "mamode": mamode},
        )

    def mcgd(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        c: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mcgd；输入：close；输出：mcgd。参数按审核目录校验。"""
        return self._call(
            "ta.mcgd",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "c": c},
        )

    def md(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.md；输入：close；输出：md。参数按审核目录校验。"""
        return self._call(
            "ta.md", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def median(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.median；输入：close；输出：median。参数按审核目录校验。"""
        return self._call(
            "ta.median", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def medprice(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.medprice；输入：high, low；输出：medprice。参数按审核目录校验。"""
        return self._call("ta.medprice", "", None, inputs, backend, required_outputs, {})

    def mfi(
        self,
        *,
        length: int = 14,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mfi；输入：high, low, close, volume；输出：mfi。参数按审核目录校验。"""
        return self._call(
            "ta.mfi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def midpoint(
        self,
        source: Source | None = None,
        *,
        length: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.midpoint；输入：close；输出：midpoint。参数按审核目录校验。"""
        return self._call(
            "ta.midpoint", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def midprice(
        self,
        *,
        length: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.midprice；输入：high, low；输出：midprice。参数按审核目录校验。"""
        return self._call(
            "ta.midprice", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def minus_dm(
        self,
        *,
        length: int = 14,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.minus_dm；输入：high, low；输出：minus_dm。参数按审核目录校验。"""
        return self._call(
            "ta.minus_dm",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def mmar(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MmarResult:
        """ta.mmar；输入：close；输出：ma1, ma2, ma3, ma4, ma5, ma6。参数按审核目录校验。"""
        return MmarResult(
            self._call(
                "ta.mmar", "close", source, inputs, backend, required_outputs, {"length": length}
            )
        )

    def mode(
        self,
        source: Source | None = None,
        *,
        length: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mode；输入：close；输出：mode。参数按审核目录校验。"""
        return self._call(
            "ta.mode", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def mom(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.mom；输入：close；输出：mom。参数按审核目录校验。"""
        return self._call(
            "ta.mom", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def msw(
        self,
        source: Source | None = None,
        *,
        period: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> MswResult:
        """ta.msw；输入：close；输出：sine, lead_sine。参数按审核目录校验。"""
        return MswResult(
            self._call(
                "ta.msw", "close", source, inputs, backend, required_outputs, {"period": period}
            )
        )

    def natr(
        self,
        *,
        length: int = 14,
        scalar: int = 100,
        mamode: str = "rma",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.natr；输入：high, low, close；输出：natr。参数按审核目录校验。"""
        return self._call(
            "ta.natr",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar, "mamode": mamode, "drift": drift},
        )

    def nvi(
        self,
        *,
        length: int = 1,
        initial: int = 1000,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.nvi；输入：close, volume；输出：nvi。参数按审核目录校验。"""
        return self._call(
            "ta.nvi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "initial": initial},
        )

    def obv(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.obv；输入：close, volume；输出：obv。参数按审核目录校验。"""
        return self._call("ta.obv", "", None, inputs, backend, required_outputs, {})

    def ohlc4(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ohlc4；输入：open_, high, low, close；输出：ohlc4。参数按审核目录校验。"""
        return self._call("ta.ohlc4", "", None, inputs, backend, required_outputs, {})

    def pdist(
        self,
        *,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pdist；输入：open_, high, low, close；输出：pdist。参数按审核目录校验。"""
        return self._call("ta.pdist", "", None, inputs, backend, required_outputs, {"drift": drift})

    def percent_return(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        cumulative: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.percent_return；输入：close；输出：percent_return。参数按审核目录校验。"""
        return self._call(
            "ta.percent_return",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "cumulative": cumulative},
        )

    def percentile_linear_interpolation(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        percentage: float = 50,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.percentile_linear_interpolation；输入：source；输出：percentile_linear_interpolation。参数按审核目录校验。"""
        return self._call(
            "ta.percentile_linear_interpolation",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "percentage": percentage},
        )

    def percentile_nearest_rank(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        percentage: float = 50,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.percentile_nearest_rank；输入：source；输出：percentile_nearest_rank。参数按审核目录校验。"""
        return self._call(
            "ta.percentile_nearest_rank",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "percentage": percentage},
        )

    def percentrank(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.percentrank；输入：source；输出：percentrank。参数按审核目录校验。"""
        return self._call(
            "ta.percentrank",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length},
        )

    def pgo(
        self,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pgo；输入：high, low, close；输出：pgo。参数按审核目录校验。"""
        return self._call("ta.pgo", "", None, inputs, backend, required_outputs, {"length": length})

    def pivot_points(
        self,
        *,
        method: str = "traditional",
        developing: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PivotPointsResult:
        """ta.pivot_points；输入：open_, high, low, close, anchor；输出：p, r1, s1, r2, s2, r3, s3, r4, s4, r5, s5。参数按审核目录校验。"""
        return PivotPointsResult(
            self._call(
                "ta.pivot_points",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"method": method, "developing": developing},
            )
        )

    def pivothigh(
        self,
        source: Source | None = None,
        *,
        left: int = 2,
        right: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PivothighResult:
        """ta.pivothigh；输入：high；输出：value, pivot_bar, confirmed_at。参数按审核目录校验。"""
        return PivothighResult(
            self._call(
                "ta.pivothigh",
                "high",
                source,
                inputs,
                backend,
                required_outputs,
                {"left": left, "right": right},
            )
        )

    def pivotlow(
        self,
        source: Source | None = None,
        *,
        left: int = 2,
        right: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PivotlowResult:
        """ta.pivotlow；输入：low；输出：value, pivot_bar, confirmed_at。参数按审核目录校验。"""
        return PivotlowResult(
            self._call(
                "ta.pivotlow",
                "low",
                source,
                inputs,
                backend,
                required_outputs,
                {"left": left, "right": right},
            )
        )

    def plus_dm(
        self,
        *,
        length: int = 14,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.plus_dm；输入：high, low；输出：plus_dm。参数按审核目录校验。"""
        return self._call(
            "ta.plus_dm",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def pmax(
        self,
        *,
        length: int = 10,
        multiplier: float = 3.0,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pmax；输入：high, low, close；输出：pmax。参数按审核目录校验。"""
        return self._call(
            "ta.pmax",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "multiplier": multiplier, "mamode": mamode},
        )

    def pmo(
        self,
        source: Source | None = None,
        *,
        length: int = 35,
        smooth: int = 20,
        signal: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PmoResult:
        """ta.pmo；输入：close；输出：pmo, signal。参数按审核目录校验。"""
        return PmoResult(
            self._call(
                "ta.pmo",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "smooth": smooth, "signal": signal},
            )
        )

    def po(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.po；输入：close；输出：po。参数按审核目录校验。"""
        return self._call(
            "ta.po", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def ppo(
        self,
        source: Source | None = None,
        *,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        scalar: int = 100,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PpoResult:
        """ta.ppo；输入：close；输出：ppo, histogram, signal。参数按审核目录校验。"""
        return PpoResult(
            self._call(
                "ta.ppo",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal, "scalar": scalar, "mamode": mamode},
            )
        )

    def psar(
        self,
        *,
        af0: float = 0.02,
        af: float = 0.02,
        max_af: float = 0.2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PsarResult:
        """ta.psar；输入：high, low, close；输出：long, short, acceleration, reversal。参数按审核目录校验。"""
        return PsarResult(
            self._call(
                "ta.psar",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"af0": af0, "af": af, "max_af": max_af},
            )
        )

    def psl(
        self,
        source: Source | None = None,
        *,
        length: int = 12,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.psl；输入：close；输出：psl。参数按审核目录校验。"""
        return self._call(
            "ta.psl",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar, "drift": drift},
        )

    def pvi(
        self,
        *,
        length: int = 1,
        initial: int = 1000,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pvi；输入：close, volume；输出：pvi。参数按审核目录校验。"""
        return self._call(
            "ta.pvi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "initial": initial},
        )

    def pvo(
        self,
        source: Source | None = None,
        *,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> PvoResult:
        """ta.pvo；输入：volume；输出：pvo, histogram, signal。参数按审核目录校验。"""
        return PvoResult(
            self._call(
                "ta.pvo",
                "volume",
                source,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal, "scalar": scalar},
            )
        )

    def pvol(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pvol；输入：close, volume；输出：pvol。参数按审核目录校验。"""
        return self._call("ta.pvol", "", None, inputs, backend, required_outputs, {})

    def pvr(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pvr；输入：close, volume；输出：pvr。参数按审核目录校验。"""
        return self._call("ta.pvr", "", None, inputs, backend, required_outputs, {})

    def pvt(
        self,
        *,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pvt；输入：close, volume；输出：pvt。参数按审核目录校验。"""
        return self._call("ta.pvt", "", None, inputs, backend, required_outputs, {"drift": drift})

    def pwma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        asc: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.pwma；输入：close；输出：pwma。参数按审核目录校验。"""
        return self._call(
            "ta.pwma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "asc": asc},
        )

    def qqe(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        smooth: int = 5,
        factor: float = 4.236,
        mamode: str = "ema",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> QqeResult:
        """ta.qqe；输入：close；输出：qqe, smoothed_rsi, long, short, basis_long, basis_short, direction。参数按审核目录校验。"""
        return QqeResult(
            self._call(
                "ta.qqe",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {
                    "length": length,
                    "smooth": smooth,
                    "factor": factor,
                    "mamode": mamode,
                    "drift": drift,
                },
            )
        )

    def qstick(
        self,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.qstick；输入：open_, close；输出：qstick。参数按审核目录校验。"""
        return self._call(
            "ta.qstick", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def quantile(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        q: float = 0.5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.quantile；输入：close；输出：quantile。参数按审核目录校验。"""
        return self._call(
            "ta.quantile",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "q": q},
        )

    def rainbow(
        self,
        source: Source | None = None,
        *,
        length: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> RainbowResult:
        """ta.rainbow；输入：close；输出：ma1, ma2, ma3, ma4, ma5, ma6, ma7, ma8, ma9, ma10。参数按审核目录校验。"""
        return RainbowResult(
            self._call(
                "ta.rainbow", "close", source, inputs, backend, required_outputs, {"length": length}
            )
        )

    def range(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.range；输入：source；输出：range。参数按审核目录校验。"""
        return self._call(
            "ta.range", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def rci(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rci；输入：close；输出：rci。参数按审核目录校验。"""
        return self._call(
            "ta.rci", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def rising(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rising；输入：source；输出：rising。参数按审核目录校验。"""
        return self._call(
            "ta.rising", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def rma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rma；输入：close；输出：rma。参数按审核目录校验。"""
        return self._call(
            "ta.rma", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def rmi(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        momentum: int = 5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rmi；输入：close；输出：rmi。参数按审核目录校验。"""
        return self._call(
            "ta.rmi",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "momentum": momentum},
        )

    def roc(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.roc；输入：close；输出：roc。参数按审核目录校验。"""
        return self._call(
            "ta.roc",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar},
        )

    def rocp(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rocp；输入：close；输出：rocp。参数按审核目录校验。"""
        return self._call(
            "ta.rocp", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def rocr(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rocr；输入：close；输出：rocr。参数按审核目录校验。"""
        return self._call(
            "ta.rocr", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def rocr100(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rocr100；输入：close；输出：rocr100。参数按审核目录校验。"""
        return self._call(
            "ta.rocr100", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def rolling_count(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rolling_count；输入：condition；输出：rolling_count。参数按审核目录校验。"""
        return self._call(
            "ta.rolling_count",
            "condition",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length},
        )

    def rolling_sum(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rolling_sum；输入：source；输出：rolling_sum。参数按审核目录校验。"""
        return self._call(
            "ta.rolling_sum",
            "source",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length},
        )

    def rsi(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rsi；输入：close；输出：rsi。参数按审核目录校验。"""
        return self._call(
            "ta.rsi",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar, "drift": drift},
        )

    def rsx(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rsx；输入：close；输出：rsx。参数按审核目录校验。"""
        return self._call(
            "ta.rsx", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def running_max(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.running_max；输入：source；输出：running_max。参数按审核目录校验。"""
        return self._call("ta.running_max", "source", source, inputs, backend, required_outputs, {})

    def running_min(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.running_min；输入：source；输出：running_min。参数按审核目录校验。"""
        return self._call("ta.running_min", "source", source, inputs, backend, required_outputs, {})

    def rvgi(
        self,
        *,
        length: int = 14,
        swma_length: int = 4,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> RvgiResult:
        """ta.rvgi；输入：open_, high, low, close；输出：histogram, rvgi, signal。参数按审核目录校验。"""
        return RvgiResult(
            self._call(
                "ta.rvgi",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "swma_length": swma_length},
            )
        )

    def rvi(
        self,
        *,
        length: int = 14,
        scalar: int = 100,
        refined: bool = False,
        thirds: bool = False,
        mamode: str = "ema",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rvi；输入：close, high, low；输出：rvi。参数按审核目录校验。"""
        return self._call(
            "ta.rvi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {
                "length": length,
                "scalar": scalar,
                "refined": refined,
                "thirds": thirds,
                "mamode": mamode,
                "drift": drift,
            },
        )

    def rvol(
        self,
        source: Source | None = None,
        *,
        length: int = 20,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.rvol；输入：volume；输出：rvol。参数按审核目录校验。"""
        return self._call(
            "ta.rvol", "volume", source, inputs, backend, required_outputs, {"length": length}
        )

    def sarext(
        self,
        *,
        startvalue: float = 0.0,
        offsetonreverse: float = 0.0,
        accelerationinitlong: float = 0.02,
        accelerationlong: float = 0.02,
        accelerationmaxlong: float = 0.2,
        accelerationinitshort: float = 0.02,
        accelerationshort: float = 0.02,
        accelerationmaxshort: float = 0.2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.sarext；输入：high, low；输出：sarext。参数按审核目录校验。"""
        return self._call(
            "ta.sarext",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {
                "startvalue": startvalue,
                "offsetonreverse": offsetonreverse,
                "accelerationinitlong": accelerationinitlong,
                "accelerationlong": accelerationlong,
                "accelerationmaxlong": accelerationmaxlong,
                "accelerationinitshort": accelerationinitshort,
                "accelerationshort": accelerationshort,
                "accelerationmaxshort": accelerationmaxshort,
            },
        )

    def shift(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.shift；输入：source；输出：shift。参数按审核目录校验。"""
        return self._call(
            "ta.shift", "source", source, inputs, backend, required_outputs, {"length": length}
        )

    def short_run(
        self,
        *,
        length: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.short_run；输入：fast, slow；输出：short_run。参数按审核目录校验。"""
        return self._call(
            "ta.short_run", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def sinwma(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.sinwma；输入：close；输出：sinwma。参数按审核目录校验。"""
        return self._call(
            "ta.sinwma", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def skew(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.skew；输入：close；输出：skew。参数按审核目录校验。"""
        return self._call(
            "ta.skew", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def slope(
        self,
        source: Source | None = None,
        *,
        length: int = 1,
        as_angle: bool = False,
        to_degrees: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.slope；输入：close；输出：slope。参数按审核目录校验。"""
        return self._call(
            "ta.slope",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "as_angle": as_angle, "to_degrees": to_degrees},
        )

    def sma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.sma；输入：close；输出：sma。参数按审核目录校验。"""
        return self._call(
            "ta.sma", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def smc_sweep(
        self,
        *,
        length: int = 15,
        wick_mult: float = 1.5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.smc_sweep；输入：open_, high, low, close；输出：smc_sweep。参数按审核目录校验。"""
        return self._call(
            "ta.smc_sweep",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "wick_mult": wick_mult},
        )

    def smi(
        self,
        source: Source | None = None,
        *,
        fast: int = 5,
        slow: int = 20,
        signal: int = 5,
        scalar: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> SmiResult:
        """ta.smi；输入：close；输出：smi, signal, oscillator。参数按审核目录校验。"""
        return SmiResult(
            self._call(
                "ta.smi",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal, "scalar": scalar},
            )
        )

    def smi_stochastic(
        self,
        *,
        length: int = 13,
        smooth: int = 25,
        double: int = 2,
        signal: int = 3,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> SmiStochasticResult:
        """ta.smi_stochastic；输入：high, low, close；输出：smi, signal。参数按审核目录校验。"""
        return SmiStochasticResult(
            self._call(
                "ta.smi_stochastic",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "smooth": smooth, "double": double, "signal": signal},
            )
        )

    def squeeze(
        self,
        *,
        bb_length: int = 20,
        bb_std: float = 2.0,
        kc_length: int = 20,
        kc_scalar: float = 1.5,
        mom_length: int = 12,
        mom_smooth: int = 6,
        use_tr: bool = True,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> SqueezeResult:
        """ta.squeeze；输入：high, low, close；输出：squeeze, on, off, none。参数按审核目录校验。"""
        return SqueezeResult(
            self._call(
                "ta.squeeze",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "bb_length": bb_length,
                    "bb_std": bb_std,
                    "kc_length": kc_length,
                    "kc_scalar": kc_scalar,
                    "mom_length": mom_length,
                    "mom_smooth": mom_smooth,
                    "use_tr": use_tr,
                    "mamode": mamode,
                },
            )
        )

    def squeeze_pro(
        self,
        *,
        bb_length: int = 20,
        bb_std: float = 2.0,
        kc_length: int = 20,
        kc_scalar_wide: int = 2,
        kc_scalar_normal: float = 1.5,
        kc_scalar_narrow: int = 1,
        mom_length: int = 12,
        mom_smooth: int = 6,
        use_tr: bool = True,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> SqueezeProResult:
        """ta.squeeze_pro；输入：high, low, close；输出：squeeze, on_wide, on_normal, on_narrow, off, none。参数按审核目录校验。"""
        return SqueezeProResult(
            self._call(
                "ta.squeeze_pro",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {
                    "bb_length": bb_length,
                    "bb_std": bb_std,
                    "kc_length": kc_length,
                    "kc_scalar_wide": kc_scalar_wide,
                    "kc_scalar_normal": kc_scalar_normal,
                    "kc_scalar_narrow": kc_scalar_narrow,
                    "mom_length": mom_length,
                    "mom_smooth": mom_smooth,
                    "use_tr": use_tr,
                    "mamode": mamode,
                },
            )
        )

    def ssf(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        poles: int = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ssf；输入：close；输出：ssf。参数按审核目录校验。"""
        return self._call(
            "ta.ssf",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "poles": poles},
        )

    def starc(
        self,
        *,
        length: int = 5,
        atr_length: int = 15,
        multiplier: float = 2,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> StarcResult:
        """ta.starc；输入：high, low, close；输出：middle, upper, lower。参数按审核目录校验。"""
        return StarcResult(
            self._call(
                "ta.starc",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "atr_length": atr_length, "multiplier": multiplier},
            )
        )

    def stc(
        self,
        source: Source | None = None,
        *,
        tclength: int = 10,
        fast: int = 12,
        slow: int = 26,
        factor: float = 0.5,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> StcResult:
        """ta.stc；输入：close；输出：stc, macd, stochastic。参数按审核目录校验。"""
        return StcResult(
            self._call(
                "ta.stc",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"tclength": tclength, "fast": fast, "slow": slow, "factor": factor},
            )
        )

    def stderr(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        ddof: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.stderr；输入：close；输出：stderr。参数按审核目录校验。"""
        return self._call(
            "ta.stderr",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "ddof": ddof},
        )

    def stdev(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        ddof: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.stdev；输入：close；输出：stdev。参数按审核目录校验。"""
        return self._call(
            "ta.stdev",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "ddof": ddof},
        )

    def stoch(
        self,
        *,
        k: int = 14,
        d: int = 3,
        smooth_k: int = 3,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> StochResult:
        """ta.stoch；输入：high, low, close；输出：k, d。参数按审核目录校验。"""
        return StochResult(
            self._call(
                "ta.stoch",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"k": k, "d": d, "smooth_k": smooth_k, "mamode": mamode},
            )
        )

    def stochf(
        self,
        *,
        fastk: int = 5,
        fastd: int = 3,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> StochfResult:
        """ta.stochf；输入：high, low, close；输出：k, d。参数按审核目录校验。"""
        return StochfResult(
            self._call(
                "ta.stochf",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"fastk": fastk, "fastd": fastd, "mamode": mamode},
            )
        )

    def stochrsi(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        rsi_length: int = 14,
        k: int = 3,
        d: int = 3,
        mamode: str = "sma",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> StochrsiResult:
        """ta.stochrsi；输入：close；输出：k, d。参数按审核目录校验。"""
        return StochrsiResult(
            self._call(
                "ta.stochrsi",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "rsi_length": rsi_length, "k": k, "d": d, "mamode": mamode},
            )
        )

    def supertrend(
        self,
        *,
        length: int = 7,
        multiplier: float = 3.0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> SupertrendResult:
        """ta.supertrend；输入：high, low, close；输出：trend, direction, long, short。参数按审核目录校验。"""
        return SupertrendResult(
            self._call(
                "ta.supertrend",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "multiplier": multiplier},
            )
        )

    def swma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        asc: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.swma；输入：close；输出：swma。参数按审核目录校验。"""
        return self._call(
            "ta.swma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "asc": asc},
        )

    def t3(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        a: float = 0.7,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.t3；输入：close；输出：t3。参数按审核目录校验。"""
        return self._call(
            "ta.t3", "close", source, inputs, backend, required_outputs, {"length": length, "a": a}
        )

    def td_seq(
        self,
        source: Source | None = None,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> TdSeqResult:
        """ta.td_seq；输入：close；输出：up, down。参数按审核目录校验。"""
        return TdSeqResult(
            self._call("ta.td_seq", "close", source, inputs, backend, required_outputs, {})
        )

    def tema(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.tema；输入：close；输出：tema。参数按审核目录校验。"""
        return self._call(
            "ta.tema", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def thermo(
        self,
        *,
        length: int = 20,
        long: int = 2,
        short: float = 0.5,
        mamode: str = "ema",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> ThermoResult:
        """ta.thermo；输入：high, low；输出：thermo, average, long, short。参数按审核目录校验。"""
        return ThermoResult(
            self._call(
                "ta.thermo",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "long": long, "short": short, "mamode": mamode, "drift": drift},
            )
        )

    def trima(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.trima；输入：close；输出：trima。参数按审核目录校验。"""
        return self._call(
            "ta.trima", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def trix(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        signal: int = 9,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> TrixResult:
        """ta.trix；输入：close；输出：trix, signal。参数按审核目录校验。"""
        return TrixResult(
            self._call(
                "ta.trix",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "signal": signal, "scalar": scalar, "drift": drift},
            )
        )

    def trixh(
        self,
        source: Source | None = None,
        *,
        length: int = 18,
        signal: int = 9,
        scalar: int = 100,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> TrixhResult:
        """ta.trixh；输入：close；输出：trix, signal, histogram。参数按审核目录校验。"""
        return TrixhResult(
            self._call(
                "ta.trixh",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {"length": length, "signal": signal, "scalar": scalar, "drift": drift},
            )
        )

    def true_range(
        self,
        *,
        drift: int = 1,
        handle_na: bool = False,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.true_range；输入：high, low, close；输出：true_range。参数按审核目录校验。"""
        return self._call(
            "ta.true_range",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"drift": drift, "handle_na": handle_na},
        )

    def tsf(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.tsf；输入：close；输出：tsf。参数按审核目录校验。"""
        return self._call(
            "ta.tsf", "close", source, inputs, backend, required_outputs, {"length": length}
        )

    def tsi(
        self,
        source: Source | None = None,
        *,
        fast: int = 13,
        slow: int = 25,
        signal: int = 13,
        scalar: int = 100,
        mamode: str = "ema",
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> TsiResult:
        """ta.tsi；输入：close；输出：tsi, signal。参数按审核目录校验。"""
        return TsiResult(
            self._call(
                "ta.tsi",
                "close",
                source,
                inputs,
                backend,
                required_outputs,
                {
                    "fast": fast,
                    "slow": slow,
                    "signal": signal,
                    "scalar": scalar,
                    "mamode": mamode,
                    "drift": drift,
                },
            )
        )

    def tsignals(
        self,
        source: Source | None = None,
        *,
        asbool: bool = False,
        trade_offset: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> TsignalsResult:
        """ta.tsignals；输入：trend；输出：trend, trades, entries, exits。参数按审核目录校验。"""
        return TsignalsResult(
            self._call(
                "ta.tsignals",
                "trend",
                source,
                inputs,
                backend,
                required_outputs,
                {"asbool": asbool, "trade_offset": trade_offset},
            )
        )

    def ttm_trend(
        self,
        *,
        length: int = 6,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ttm_trend；输入：high, low, close；输出：ttm_trend。参数按审核目录校验。"""
        return self._call(
            "ta.ttm_trend", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def typprice(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.typprice；输入：high, low, close；输出：typprice。参数按审核目录校验。"""
        return self._call("ta.typprice", "", None, inputs, backend, required_outputs, {})

    def ui(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        scalar: int = 100,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.ui；输入：close；输出：ui。参数按审核目录校验。"""
        return self._call(
            "ta.ui",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "scalar": scalar},
        )

    def uo(
        self,
        *,
        fast: int = 7,
        medium: int = 14,
        slow: int = 28,
        fast_w: float = 4.0,
        medium_w: float = 2.0,
        slow_w: float = 1.0,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.uo；输入：high, low, close；输出：uo。参数按审核目录校验。"""
        return self._call(
            "ta.uo",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {
                "fast": fast,
                "medium": medium,
                "slow": slow,
                "fast_w": fast_w,
                "medium_w": medium_w,
                "slow_w": slow_w,
                "drift": drift,
            },
        )

    def valuewhen(
        self,
        condition: Source | None = None,
        source: Source | None = None,
        *,
        occurrence: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.valuewhen；输入：condition, source；输出：valuewhen。参数按审核目录校验。"""
        return self._call_inputs(
            "ta.valuewhen",
            {"condition": condition, "source": source},
            inputs,
            backend,
            required_outputs,
            {"occurrence": occurrence},
        )

    def variance(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        ddof: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.variance；输入：close；输出：variance。参数按审核目录校验。"""
        return self._call(
            "ta.variance",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "ddof": ddof},
        )

    def vfi(
        self,
        *,
        length: int = 130,
        coef: float = 0.2,
        vcoef: float = 2.5,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vfi；输入：close, volume；输出：vfi。参数按审核目录校验。"""
        return self._call(
            "ta.vfi",
            "",
            None,
            inputs,
            backend,
            required_outputs,
            {"length": length, "coef": coef, "vcoef": vcoef, "mamode": mamode},
        )

    def vhf(
        self,
        source: Source | None = None,
        *,
        length: int = 28,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vhf；输入：close；输出：vhf。参数按审核目录校验。"""
        return self._call(
            "ta.vhf",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def vidya(
        self,
        source: Source | None = None,
        *,
        length: int = 14,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vidya；输入：close；输出：vidya。参数按审核目录校验。"""
        return self._call(
            "ta.vidya",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "drift": drift},
        )

    def volatility_stop(
        self,
        *,
        length: int = 7,
        multiplier: float = 3,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> VolatilityStopResult:
        """ta.volatility_stop；输入：high, low, close；输出：stop, direction。参数按审核目录校验。"""
        return VolatilityStopResult(
            self._call(
                "ta.volatility_stop",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "multiplier": multiplier},
            )
        )

    def vortex(
        self,
        *,
        length: int = 14,
        drift: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> VortexResult:
        """ta.vortex；输入：high, low, close；输出：positive, negative。参数按审核目录校验。"""
        return VortexResult(
            self._call(
                "ta.vortex",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "drift": drift},
            )
        )

    def vosc(
        self,
        source: Source | None = None,
        *,
        fast: int = 14,
        slow: int = 28,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vosc；输入：volume；输出：vosc。参数按审核目录校验。"""
        return self._call(
            "ta.vosc",
            "volume",
            source,
            inputs,
            backend,
            required_outputs,
            {"fast": fast, "slow": slow},
        )

    def vwap(
        self,
        *,
        anchor: str = "D",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vwap；输入：high, low, close, volume；输出：vwap。参数按审核目录校验。"""
        return self._call(
            "ta.vwap", "", None, inputs, backend, required_outputs, {"anchor": anchor}
        )

    def vwma(
        self,
        *,
        length: int = 10,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.vwma；输入：close, volume；输出：vwma。参数按审核目录校验。"""
        return self._call(
            "ta.vwma", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def vwmacd(
        self,
        *,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> VwmacdResult:
        """ta.vwmacd；输入：close, volume；输出：macd, histogram, signal。参数按审核目录校验。"""
        return VwmacdResult(
            self._call(
                "ta.vwmacd",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"fast": fast, "slow": slow, "signal": signal},
            )
        )

    def wad(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.wad；输入：high, low, close；输出：wad。参数按审核目录校验。"""
        return self._call("ta.wad", "", None, inputs, backend, required_outputs, {})

    def wavetrend(
        self,
        *,
        length: int = 10,
        average: int = 21,
        signal: int = 4,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> WavetrendResult:
        """ta.wavetrend；输入：high, low, close；输出：wave, signal。参数按审核目录校验。"""
        return WavetrendResult(
            self._call(
                "ta.wavetrend",
                "",
                None,
                inputs,
                backend,
                required_outputs,
                {"length": length, "average": average, "signal": signal},
            )
        )

    def wcp(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.wcp；输入：high, low, close；输出：wcp。参数按审核目录校验。"""
        return self._call("ta.wcp", "", None, inputs, backend, required_outputs, {})

    def willr(
        self,
        *,
        length: int = 14,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.willr；输入：high, low, close；输出：willr。参数按审核目录校验。"""
        return self._call(
            "ta.willr", "", None, inputs, backend, required_outputs, {"length": length}
        )

    def wma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        asc: bool = True,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.wma；输入：close；输出：wma。参数按审核目录校验。"""
        return self._call(
            "ta.wma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "asc": asc},
        )

    def wvad(
        self,
        *,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.wvad；输入：open_, high, low, close, volume；输出：wvad。参数按审核目录校验。"""
        return self._call("ta.wvad", "", None, inputs, backend, required_outputs, {})

    def xsignals(
        self,
        source: Source | None = None,
        *,
        xa: int = 0,
        xb: int = 0,
        above: bool = True,
        long: bool = True,
        asbool: bool = False,
        trade_offset: int = 0,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> XsignalsResult:
        """ta.xsignals；输入：signal；输出：trend, trades, entries, exits。参数按审核目录校验。"""
        return XsignalsResult(
            self._call(
                "ta.xsignals",
                "signal",
                source,
                inputs,
                backend,
                required_outputs,
                {
                    "xa": xa,
                    "xb": xb,
                    "above": above,
                    "long": long,
                    "asbool": asbool,
                    "trade_offset": trade_offset,
                },
            )
        )

    def zlma(
        self,
        source: Source | None = None,
        *,
        length: int = 10,
        mamode: str = "ema",
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.zlma；输入：close；输出：zlma。参数按审核目录校验。"""
        return self._call(
            "ta.zlma",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "mamode": mamode},
        )

    def zscore(
        self,
        source: Source | None = None,
        *,
        length: int = 30,
        std: int = 1,
        inputs: Inputs | None = None,
        backend: str | None = None,
        required_outputs: Sequence[str] | None = None,
    ) -> IndicatorHandle:
        """ta.zscore；输入：close；输出：zscore。参数按审核目录校验。"""
        return self._call(
            "ta.zscore",
            "close",
            source,
            inputs,
            backend,
            required_outputs,
            {"length": length, "std": std},
        )
