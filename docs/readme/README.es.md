<h1>
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../assets/brand/wordmark-white.svg">
  <img src="../assets/brand/wordmark.svg" alt="OpenBacktesting" width="300" height="36">
</picture>
</h1>

**Backtesting histórico en Python: de las reglas de estrategia a resultados que puedes examinar.**

[English](../../README.md) · [简体中文](README.zh-CN.md) · **Español** · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Escribe estrategias que se ejecutan vela a vela, evalúalas con datos históricos de mercado y examina órdenes, operaciones, capital y estadísticas de riesgo. OpenBacktesting es un paquete independiente de Python con indicadores, optimización de parámetros, informes Portfolio y exportación de datos para gráficos.

**Python 3.12–3.14** · **Versión 0.2.1** · Distribución e importación: `openbacktesting`

[Inicio rápido](#quick-start) · [Manual](https://docs.openbacktesting.com/) · [Ejemplos](https://docs.openbacktesting.com/examples/) · [Informar de un problema](https://github.com/lucidcog/openbacktesting/issues)

[![OpenBacktesting Studio](../core/_static/studio/backtest-results-light.jpg)](../core/_static/studio/backtest-results-light.jpg)

## Patrocinador principal — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) es el principal patrocinador de pago de OpenBacktesting.** Su apoyo económico contribuye a financiar este proyecto.

Pineify es un conjunto de herramientas de trading con IA para crear indicadores y estrategias en múltiples plataformas. Reúne Pine Script AI, un agente financiero, selección de acciones con IA, filtros de mercado, análisis de gráficos y herramientas MCP. [Descubre Pineify →](https://pineify.app)

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

El ejemplo utiliza datos históricos de GOOG incluidos en el paquete; no requiere descargar datos de mercado. Muestra rentabilidad, número de operaciones, caída máxima y tablas de resultados. Consulta [tu primer backtest](https://docs.openbacktesting.com/quickstart/) para seguir la explicación.

Como alternativa, instala el código fuente descargado en un entorno de Python existente:

```sh
python -m pip install .
```

Las dependencias básicas son NumPy, pandas y `pandas-ta-classic==0.8.32`. Para optimización con SAMBO, usa `python -m pip install '.[optimize]'` o `uv sync --locked --extra optimize`. Estas instrucciones instalan desde el código fuente; no presuponen una publicación en PyPI. [Detalles de compilación y distribución](https://docs.openbacktesting.com/development/).

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

`run()` devuelve una Series de pandas. Usa `result["_trades"]` para las operaciones y `result["_equity_curve"]` para el historial de capital. La [guía de resultados](https://docs.openbacktesting.com/guides/results/) incluye todos los campos y la exportación de Portfolio; los campos que empiezan por guion bajo son diagnósticos nativos, no un contrato estable entre lenguajes.

## Documentación

[Manual](https://docs.openbacktesting.com/)

El manual detallado y los ejemplos están actualmente en inglés.

| Tema | Referencia |
| --- | --- |
| Primeros pasos | [Primer backtest](https://docs.openbacktesting.com/quickstart/) · [Índice de ejemplos](https://docs.openbacktesting.com/examples/) |
| Estrategias y datos | [Ciclo de la estrategia](https://docs.openbacktesting.com/guides/author/) · [Datos de mercado](https://docs.openbacktesting.com/guides/data/) · [API principal](https://docs.openbacktesting.com/reference/core/) |
| Indicadores | [Catálogo de indicadores](https://docs.openbacktesting.com/reference/indicators/) |
| Ejecución y optimización | [Ejecutar estrategias](https://docs.openbacktesting.com/guides/runtime/) · [Experimentos de parámetros](https://docs.openbacktesting.com/guides/optimizer/) |
| Resultados y gráficos | [Resultados y Portfolio](https://docs.openbacktesting.com/guides/results/) · [Exportar datos para gráficos](https://docs.openbacktesting.com/guides/plotting/) |
| Desarrollo | [Verificación y compilación](https://docs.openbacktesting.com/development/) · [Limitaciones actuales](https://docs.openbacktesting.com/limitations/) |

## Alcance y compatibilidad

- El modelo opera con **un único activo y una única moneda de liquidación**. Los informes Portfolio describen una ejecución; no son cuentas de cartera multiactivo.
- El paquete proporciona cálculos y datos para gráficos. **No incluye un renderizador de gráficos, un motor de trading en vivo, un entorno aislado de ejecución ni un conversor de Pine Script**, y no garantiza equivalencia semántica con Pine. Ejecuta únicamente código de estrategia de confianza.
- La compatibilidad con Windows y las comparaciones completas con Pine no se han validado. Consulta las [limitaciones actuales](https://docs.openbacktesting.com/limitations/) sobre ejecución y modelado del mercado.

Tanto la distribución como la importación se llaman `openbacktesting`; no existen puntos de entrada con nombres anteriores. Los archivos pickle con rutas de módulos antiguas no se migran automáticamente, no se garantiza la lectura de archivos con identificadores de marca anteriores y los experimentos con una identidad de ejecución antigua deben repetirse. [Migración y procedencia](https://docs.openbacktesting.com/development/#provenance-and-behavioral-boundaries).

## Ayuda y contribuciones

Usa [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) para errores, preguntas y propuestas. Incluye las versiones de Python y del paquete, un ejemplo mínimo que reproduzca el problema y el comportamiento esperado frente al observado. Puedes contribuir mediante [pull requests](https://github.com/lucidcog/openbacktesting/pulls).

Antes de proponer un cambio de código, ejecuta:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consulta la [guía de desarrollo](https://docs.openbacktesting.com/development/) para todas las comprobaciones. Los cambios de comportamiento público requieren documentación, ejemplos ejecutables y validación de su ejecución. El código, los comentarios y la documentación técnica se escriben en inglés por defecto; las traducciones del README son contenido localizado intencionalmente.

## Traducciones

El [README en inglés](../../README.md) es la referencia principal. Hay traducciones al chino simplificado, español, portugués de Brasil, francés, alemán, italiano e hindi. Usa los enlaces de idioma de arriba y la [guía de traducción](TRANSLATING.md) para actualizarlas. Mantén coherentes los comandos, identificadores de API, límites funcionales y reconocimiento del patrocinador.

## Licencia y procedencia

La licencia declarada del proyecto es [Apache-2.0](../../LICENSE). Los materiales de terceros conservan sus licencias originales, incluidos los [datos de referencia de indicadores](../../tests/fixtures/indicator_expansion/README.md).
