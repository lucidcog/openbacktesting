# OpenBacktesting

**Backtesting histórico en Python: de las reglas de estrategia a resultados que puedes examinar.**

[English](../../README.md) · **Español** · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Escribe estrategias que se ejecutan vela a vela, evalúalas con datos históricos de mercado y examina órdenes, operaciones, capital y estadísticas de riesgo. OpenBacktesting es un paquete independiente de Python con indicadores, optimización de parámetros, informes Portfolio y exportación de datos para gráficos.

**Python 3.12–3.14** · **Versión 0.2.0** · Distribución e importación: `openbacktesting`

[Inicio rápido](#quick-start) · [Manual](../core/index.md) · [Ejemplos](../../examples/README.md) · [Informar de un problema](https://github.com/lucidcog/openbacktesting/issues)

## Patrocinador principal — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) es el principal patrocinador de pago de OpenBacktesting.** Su apoyo económico contribuye a financiar este proyecto.

Pineify ofrece programación de Pine Script asistida por IA y un editor visual para crear indicadores y estrategias de TradingView. [Descubre Pineify →](https://pineify.app)

## Qué puedes hacer

- **Crear estrategias:** usa un ciclo de ejecución vela a vela, entradas tipadas, indicadores integrados y funciones auxiliares combinables.
- **Examinar la ejecución:** revisa órdenes, ejecuciones, dimensionamiento de posiciones, comisiones, operaciones cerradas y lotes abiertos.
- **Analizar resultados:** consulta estadísticas en pandas, curvas de capital e informes Portfolio inmutables de cada ejecución.
- **Comparar parámetros:** realiza búsquedas en cuadrícula u optimización opcional con SAMBO, guarda experimentos y exporta datos para tu propio sistema de gráficos.

<a name="quick-start"></a>

## Inicio rápido

Instala [uv](https://docs.astral.sh/uv/getting-started/installation/) y usa Python `>=3.12,<3.15`. En una terminal:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

El ejemplo utiliza datos históricos de GOOG incluidos en el paquete; no requiere descargar datos de mercado. Muestra rentabilidad, número de operaciones, caída máxima y tablas de resultados. Consulta [tu primer backtest](../core/quickstart.md) para seguir la explicación.

Como alternativa, instala el código fuente descargado en un entorno de Python existente:

```sh
python -m pip install .
```

Las dependencias básicas son NumPy, pandas y `pandas-ta-classic==0.8.32`. Para optimización con SAMBO, usa `python -m pip install '.[optimize]'` o `uv sync --locked --extra optimize`. Estas instrucciones instalan desde el código fuente; no presuponen una publicación en PyPI. [Detalles de compilación y distribución](../core/development.md).

## Backtest mínimo

Guarda lo siguiente como `quickstart.py` en la raíz del repositorio y ejecuta `uv run --locked python quickstart.py`:

```python
from openbacktesting import Backtest, Strategy
from openbacktesting.test import GOOG


class BuyAndHold(Strategy):
    def init(self):
        pass

    def next(self):
        if self.bar_index == 0:
            self.buy(qty=1)


result = Backtest(GOOG, BuyAndHold, end_policy="close_at_last_close").run()
print(result[["Return [%]", "# Trades", "Max. Drawdown [%]"]])
```

Esta estrategia solicita una unidad en la primera vela. Por defecto, la orden se ejecuta en la apertura de la vela siguiente; `close_at_last_close` cierra la posición restante al cierre final.

`run()` devuelve una Series de pandas. Usa `result["_trades"]` para las operaciones y `result["_equity_curve"]` para el historial de capital. La [guía de resultados](../core/guides/results.md) incluye todos los campos y la exportación de Portfolio; los campos que empiezan por guion bajo son diagnósticos nativos, no un contrato estable entre lenguajes.

## Documentación

El manual detallado y los ejemplos están actualmente en inglés.

| Tema | Referencia |
| --- | --- |
| Primeros pasos | [Primer backtest](../core/quickstart.md) · [Índice de ejemplos](../../examples/README.md) |
| Estrategias y datos | [Ciclo de la estrategia](../core/guides/author.md) · [Datos de mercado](../core/guides/data.md) · [API principal](../core/reference/core.md) |
| Indicadores | [Catálogo de indicadores](../core/reference/indicators/index.md) |
| Ejecución y optimización | [Ejecutar estrategias](../core/guides/runtime.md) · [Experimentos de parámetros](../core/guides/optimizer.md) |
| Resultados y gráficos | [Resultados y Portfolio](../core/guides/results.md) · [Exportar datos para gráficos](../core/guides/plotting.md) |
| Desarrollo | [Verificación y compilación](../core/development.md) · [Limitaciones actuales](../core/limitations.md) |

## Alcance y compatibilidad

- El modelo opera con **un único activo y una única moneda de liquidación**. Los informes Portfolio describen una ejecución; no son cuentas de cartera multiactivo.
- El paquete proporciona cálculos y datos para gráficos. **No incluye un renderizador de gráficos, un motor de trading en vivo, un entorno aislado de ejecución ni un conversor de Pine Script**, y no garantiza equivalencia semántica con Pine. Ejecuta únicamente código de estrategia de confianza.
- La compatibilidad con Windows y las comparaciones completas con Pine no se han validado. Consulta las [limitaciones actuales](../core/limitations.md) sobre ejecución y modelado del mercado.

Tanto la distribución como la importación se llaman `openbacktesting`; no existen puntos de entrada con nombres anteriores. Los archivos pickle con rutas de módulos antiguas no se migran automáticamente, no se garantiza la lectura de archivos con identificadores de marca anteriores y los experimentos con una identidad de ejecución antigua deben repetirse. [Migración y procedencia](../core/development.md#provenance-and-behavioral-boundaries).

## Ayuda y contribuciones

Usa [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) para errores, preguntas y propuestas. Incluye las versiones de Python y del paquete, un ejemplo mínimo que reproduzca el problema y el comportamiento esperado frente al observado. Puedes contribuir mediante [pull requests](https://github.com/lucidcog/openbacktesting/pulls).

Antes de proponer un cambio de código, ejecuta:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consulta la [guía de desarrollo](../core/development.md) para todas las comprobaciones. Los cambios de comportamiento público requieren documentación, ejemplos ejecutables y validación de su ejecución. El código, los comentarios y la documentación técnica se escriben en inglés por defecto; las traducciones del README son contenido localizado intencionalmente.

## Traducciones

El [README en inglés](../../README.md) es la referencia principal. Hay traducciones al español, portugués de Brasil, francés, alemán, italiano e hindi. Usa los enlaces de idioma de arriba y la [guía de traducción](TRANSLATING.md) para actualizarlas. Mantén coherentes los comandos, identificadores de API, límites funcionales y reconocimiento del patrocinador.

## Licencia y procedencia

La licencia declarada del proyecto es [Apache-2.0](../../LICENSE). Los materiales de terceros conservan sus licencias originales, incluidos los [datos de referencia de indicadores](../../tests/fixtures/indicator_expansion/README.md).

El [manifiesto de fuentes](../../source-manifest.json) registra adaptaciones de una [versión del proyecto de origen bajo AGPL-3.0](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/LICENSE.md). La declaración Apache-2.0 no sustituye esas condiciones; distribuir el código derivado únicamente bajo Apache-2.0 requiere autorización aparte. El [manifiesto de extracción](../../extraction-manifest.json) registra la versión fuente directa y la correspondencia de rutas.
