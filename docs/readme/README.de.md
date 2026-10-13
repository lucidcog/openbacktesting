# OpenBacktesting

**Historisches Backtesting in Python – von Strategieregeln zu nachvollziehbaren Ergebnissen.**

[English](../../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md) · **Deutsch** · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Schreibe Strategien, die Kerze für Kerze ausgeführt werden, prüfe sie anhand historischer Marktdaten und untersuche Orders, Trades, Eigenkapital und Risikokennzahlen. OpenBacktesting ist ein eigenständiges Python-Paket mit Indikatoren, Parameteroptimierung, Portfolio-Berichten und dem Export von Daten für Diagramme.

**Python 3.12–3.14** · **Version 0.2.0** · Distributions- und Importname: `openbacktesting`

[Schnellstart](#quick-start) · [Handbuch](../core/index.md) · [Beispiele](../../examples/README.md) · [Problem melden](https://github.com/lucidcog/openbacktesting/issues)

## Hauptsponsor — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) ist der wichtigste zahlende Sponsor von OpenBacktesting.** Seine finanzielle Unterstützung trägt zur Finanzierung des Projekts bei.

Pineify ist ein KI-Trading-Toolkit zum Erstellen von Indikatoren und Strategien für verschiedene Plattformen. Es vereint Pine Script AI, einen Finanzagenten, KI-gestützte Aktienauswahl, Markt-Screening, Chartanalyse und MCP-Tools. [Pineify entdecken →](https://pineify.app)

## Funktionen

- **Strategien entwickeln:** nutze einen Ausführungszyklus pro Kerze, typisierte Eingaben, integrierte Indikatoren und kombinierbare Hilfsfunktionen.
- **Ausführung untersuchen:** prüfe Orders, Ausführungen, Positionsgrößen, Gebühren, geschlossene Trades und offene Lots.
- **Ergebnisse analysieren:** nutze pandas-Statistiken, Eigenkapitalkurven und unveränderliche Portfolio-Berichte für jeden Lauf.
- **Parameter vergleichen:** führe Rastersuchen oder optionale SAMBO-Optimierung durch, speichere Experimente und exportiere Daten für deinen eigenen Diagramm-Renderer.

<a name="quick-start"></a>

## Schnellstart

Installiere [uv](https://docs.astral.sh/uv/getting-started/installation/) und verwende Python `>=3.12,<3.15`. Führe im Terminal Folgendes aus:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

Das Beispiel verwendet mitgelieferte historische GOOG-Daten; ein Download von Marktdaten ist nicht erforderlich. Es gibt Rendite, Anzahl der Trades, maximalen Drawdown und Ergebnistabellen aus. Die Anleitung [dein erster Backtest](../core/quickstart.md) erläutert die Schritte.

Alternativ kannst du den ausgecheckten Quellcode in einer bestehenden Python-Umgebung installieren:

```sh
python -m pip install .
```

Die Basisabhängigkeiten sind NumPy, pandas und `pandas-ta-classic==0.8.32`. Verwende für SAMBO-Optimierung `python -m pip install '.[optimize]'` oder `uv sync --locked --extra optimize`. Diese Anweisungen installieren aus dem Quellcode; sie setzen keine Veröffentlichung auf PyPI voraus. [Details zu Build und Distribution](../core/development.md).

## Minimaler Backtest

Speichere diesen Code als `quickstart.py` im Stammverzeichnis des Repositorys und führe `uv run --locked python quickstart.py` aus:

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

Die Strategie fordert in der ersten Kerze den Kauf einer Einheit an. Standardmäßig wird die Order zur Eröffnung der nächsten Kerze ausgeführt; `close_at_last_close` schließt die verbleibende Position zum letzten Schlusskurs.

`run()` liefert eine pandas Series. Verwende `result["_trades"]` für Trades und `result["_equity_curve"]` für den Eigenkapitalverlauf. Der [Ergebnisleitfaden](../core/guides/results.md) enthält alle Felder und den Portfolio-Export; Felder mit führendem Unterstrich sind native Diagnosedaten und kein stabiler sprachübergreifender Vertrag.

## Dokumentation

Das ausführliche Handbuch und die Beispiele sind derzeit auf Englisch.

| Thema | Referenz |
| --- | --- |
| Einstieg | [Erster Backtest](../core/quickstart.md) · [Beispielübersicht](../../examples/README.md) |
| Strategien und Daten | [Strategie-Lebenszyklus](../core/guides/author.md) · [Marktdaten](../core/guides/data.md) · [Kern-API](../core/reference/core.md) |
| Indikatoren | [Indikatorkatalog](../core/reference/indicators/index.md) |
| Ausführung und Optimierung | [Strategien ausführen](../core/guides/runtime.md) · [Parameterexperimente](../core/guides/optimizer.md) |
| Ergebnisse und Diagramme | [Ergebnisse und Portfolio](../core/guides/results.md) · [Diagrammdaten exportieren](../core/guides/plotting.md) |
| Entwicklung | [Prüfungen und Builds](../core/development.md) · [Aktuelle Einschränkungen](../core/limitations.md) |

## Umfang und Kompatibilität

- Das Handelsmodell verwendet **einen einzelnen Vermögenswert und eine einzelne Abrechnungswährung**. Portfolio-Berichte beschreiben einen Lauf; sie sind keine Konten für Portfolios mit mehreren Vermögenswerten.
- Das Paket stellt Berechnungen und Diagrammdaten bereit. Es enthält **keinen Diagramm-Renderer, keine Live-Trading-Engine, keine Code-Sandbox und keinen Pine-Script-Konverter** und verspricht keine mit Pine identische Semantik. Führe nur vertrauenswürdigen Strategiecode aus.
- Windows-Unterstützung und vollständige Vergleiche mit Pine wurden nicht validiert. Die [aktuellen Einschränkungen](../core/limitations.md) beschreiben die Grenzen von Ausführung und Marktmodell.

Distributions- und Importname lauten `openbacktesting`; Einstiegspunkte unter früheren Namen gibt es nicht. Pickle-Dateien mit alten Modulpfaden werden nicht automatisch migriert, die Lesbarkeit von Archiven mit früheren Markenkennungen ist nicht garantiert und Experimente mit einer alten Ausführungsidentität müssen erneut ausgeführt werden. [Migration und Herkunft](../core/development.md#provenance-and-behavioral-boundaries).

## Hilfe und Beiträge

Nutze [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) für Fehler, Fragen und Funktionswünsche. Gib deine Python- und Paketversion, ein minimales Beispiel zur Reproduktion sowie erwartetes und tatsächliches Verhalten an. Beiträge über [Pull Requests](https://github.com/lucidcog/openbacktesting/pulls) sind willkommen.

Führe vor dem Einreichen einer Codeänderung Folgendes aus:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Alle Prüfungen findest du im [Entwicklungsleitfaden](../core/development.md). Änderungen am öffentlichen Verhalten erfordern passende Dokumentation, ausführbare Beispiele und eine Prüfung ihrer Ausführung. Code, Kommentare und technische Dokumentation sind standardmäßig auf Englisch; README-Übersetzungen sind bewusst lokalisierte Inhalte.

## Übersetzungen

Die [englische README](../../README.md) ist die maßgebliche Fassung. Übersetzungen gibt es auf vereinfachtem Chinesisch, Spanisch, brasilianischem Portugiesisch, Französisch, Deutsch, Italienisch und Hindi. Nutze die Sprachlinks oben und den [Übersetzungsleitfaden](TRANSLATING.md) für Aktualisierungen. Befehle, API-Bezeichner, Funktionsgrenzen und Sponsorenhinweise müssen in allen Sprachen übereinstimmen.

## Lizenz und Herkunft

Die deklarierte Projektlizenz ist [Apache-2.0](../../LICENSE). Materialien Dritter behalten ihre ursprünglichen Lizenzbedingungen, darunter die [Indikator-Referenzdaten](../../tests/fixtures/indicator_expansion/README.md).

Das [Quellmanifest](../../source-manifest.json) dokumentiert Anpassungen eines [AGPL-3.0-Upstream-Snapshots](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/LICENSE.md). Die Apache-2.0-Deklaration ersetzt diese Bedingungen nicht; die Verbreitung des abgeleiteten Codes ausschließlich unter Apache-2.0 erfordert eine gesonderte Genehmigung. Das [Extraktionsmanifest](../../extraction-manifest.json) dokumentiert den direkten Quellstand und die Pfadzuordnungen.
