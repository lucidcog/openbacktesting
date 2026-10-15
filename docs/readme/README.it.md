# OpenBacktesting

**Backtesting storico in Python, dalle regole della strategia a risultati che puoi esaminare.**

[English](../../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · **Italiano** · [हिन्दी](README.hi.md)

Scrivi strategie eseguite candela per candela, valutale su dati storici di mercato ed esamina ordini, operazioni, capitale e statistiche di rischio. OpenBacktesting è un pacchetto Python autonomo con indicatori, ottimizzazione dei parametri, report Portfolio ed esportazione di dati per grafici.

**Python 3.12–3.14** · **Versione 0.2.1** · Distribuzione e importazione: `openbacktesting`

[Avvio rapido](#quick-start) · [Manuale](https://docs.openbacktesting.com/) · [Esempi](https://docs.openbacktesting.com/examples/) · [Segnala un problema](https://github.com/lucidcog/openbacktesting/issues)

[![OpenBacktesting Studio](../core/_static/studio/backtest-results-light.jpg)](../core/_static/studio/backtest-results-light.jpg)

## Sponsor principale — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) è il principale sponsor pagante di OpenBacktesting.** Il suo sostegno economico contribuisce a finanziare questo progetto.

Pineify è una suite di strumenti di trading basati sull'IA per creare indicatori e strategie su più piattaforme. Riunisce Pine Script AI, un agente finanziario, selezione di azioni con l'IA, screening dei mercati, analisi dei grafici e strumenti MCP. [Scopri Pineify →](https://pineify.app)

## Funzionalità

- **Creare strategie:** usa un ciclo di esecuzione candela per candela, input tipizzati, indicatori integrati e funzioni ausiliarie componibili.
- **Esaminare l'esecuzione:** consulta ordini, eseguiti, dimensionamento delle posizioni, commissioni, operazioni chiuse e lotti aperti.
- **Analizzare i risultati:** accedi a statistiche pandas, curve del capitale e report Portfolio immutabili per ogni esecuzione.
- **Confrontare parametri:** esegui ricerche a griglia o l'ottimizzazione opzionale con SAMBO, salva esperimenti ed esporta dati per il tuo sistema di rendering.

<a name="quick-start"></a>

## Avvio rapido

Installa [uv](https://docs.astral.sh/uv/getting-started/installation/) e usa Python `>=3.12,<3.15`. Da un terminale:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

L'esempio usa i dati storici GOOG inclusi nel pacchetto; non richiede di scaricare dati di mercato. Mostra rendimento, numero di operazioni, drawdown massimo e tabelle dei risultati. Segui [il tuo primo backtest](https://docs.openbacktesting.com/quickstart/) per una spiegazione passo passo.

In alternativa, installa il codice sorgente scaricato in un ambiente Python esistente:

```sh
python -m pip install .
```

Le dipendenze di base sono NumPy, pandas e `pandas-ta-classic==0.8.32`. Per l'ottimizzazione SAMBO, usa `python -m pip install '.[optimize]'` o `uv sync --locked --extra optimize`. Queste istruzioni installano dal sorgente; non presuppongono una pubblicazione su PyPI. [Dettagli su build e distribuzione](https://docs.openbacktesting.com/development/).

## Backtest minimo

Salva questo codice come `quickstart.py` nella radice del repository ed esegui `uv run --locked python quickstart.py`:

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

La strategia richiede l'acquisto di un'unità sulla prima candela. Per impostazione predefinita, l'ordine viene eseguito all'apertura della candela successiva; `close_at_last_close` chiude la posizione residua all'ultima chiusura.

`run()` restituisce una Series pandas. Usa `result["_trades"]` per le operazioni e `result["_equity_curve"]` per lo storico del capitale. La [guida ai risultati](https://docs.openbacktesting.com/guides/results/) presenta tutti i campi e l'esportazione Portfolio; i campi con prefisso underscore sono dati diagnostici nativi, non un contratto stabile tra linguaggi.

## Documentazione

[Manuale](https://docs.openbacktesting.com/)

Il manuale dettagliato e gli esempi sono attualmente in inglese.

| Argomento | Riferimento |
| --- | --- |
| Primi passi | [Primo backtest](https://docs.openbacktesting.com/quickstart/) · [Indice degli esempi](https://docs.openbacktesting.com/examples/) |
| Strategie e dati | [Ciclo della strategia](https://docs.openbacktesting.com/guides/author/) · [Dati di mercato](https://docs.openbacktesting.com/guides/data/) · [API principale](https://docs.openbacktesting.com/reference/core/) |
| Indicatori | [Catalogo degli indicatori](https://docs.openbacktesting.com/reference/indicators/) |
| Esecuzione e ottimizzazione | [Eseguire strategie](https://docs.openbacktesting.com/guides/runtime/) · [Esperimenti sui parametri](https://docs.openbacktesting.com/guides/optimizer/) |
| Risultati e grafici | [Risultati e Portfolio](https://docs.openbacktesting.com/guides/results/) · [Esportare dati per grafici](https://docs.openbacktesting.com/guides/plotting/) |
| Sviluppo | [Verifiche e build](https://docs.openbacktesting.com/development/) · [Limiti attuali](https://docs.openbacktesting.com/limitations/) |

## Ambito e compatibilità

- Il modello di trading gestisce **un solo asset e una sola valuta di regolamento**. I report Portfolio descrivono una singola esecuzione; non sono conti di portafoglio multi-asset.
- Il pacchetto fornisce calcoli e dati per grafici. **Non include un renderer di grafici, un motore di trading dal vivo, una sandbox di esecuzione o un convertitore Pine Script**, e non promette una semantica equivalente a Pine. Esegui solo codice di strategia affidabile.
- Il supporto Windows e i confronti completi con Pine non sono stati validati. Consulta i [limiti attuali](https://docs.openbacktesting.com/limitations/) sull'esecuzione e sul modello di mercato.

Il nome di distribuzione e importazione è `openbacktesting`; non esistono punti di ingresso con nomi precedenti. I file pickle con vecchi percorsi dei moduli non vengono migrati automaticamente, la lettura degli archivi con precedenti identificatori di marca non è garantita e gli esperimenti con una vecchia identità di esecuzione devono essere ripetuti. [Migrazione e provenienza](https://docs.openbacktesting.com/development/#provenance-and-behavioral-boundaries).

## Supporto e contributi

Usa [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) per bug, domande e richieste di funzionalità. Includi le versioni di Python e del pacchetto, un esempio minimo che riproduca il problema e il comportamento atteso rispetto a quello osservato. I contributi tramite [pull request](https://github.com/lucidcog/openbacktesting/pulls) sono benvenuti.

Prima di proporre una modifica al codice, esegui:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consulta la [guida allo sviluppo](https://docs.openbacktesting.com/development/) per tutte le verifiche. Le modifiche al comportamento pubblico richiedono documentazione, esempi eseguibili e validazione della loro esecuzione. Codice, commenti e documentazione tecnica sono in inglese per impostazione predefinita; le traduzioni del README sono contenuti localizzati intenzionalmente.

## Traduzioni

Il [README inglese](../../README.md) è il riferimento principale. Sono disponibili traduzioni in cinese semplificato, spagnolo, portoghese brasiliano, francese, tedesco, italiano e hindi. Usa i collegamenti alle lingue in alto e segui la [guida alla traduzione](TRANSLATING.md) per aggiornarle. Mantieni coerenti comandi, identificatori API, limiti funzionali e riconoscimento dello sponsor.

## Licenza e provenienza

La licenza dichiarata del progetto è [Apache-2.0](../../LICENSE). I materiali di terze parti mantengono le licenze originali, inclusi i [dati di riferimento degli indicatori](../../tests/fixtures/indicator_expansion/README.md).
