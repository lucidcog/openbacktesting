# OpenBacktesting

**Backtesting histórico em Python, das regras da estratégia a resultados que você pode examinar.**

[English](../../README.md) · [Español](README.es.md) · **Português (Brasil)** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Escreva estratégias executadas candle a candle, avalie-as com dados históricos de mercado e examine ordens, operações, patrimônio e estatísticas de risco. O OpenBacktesting é um pacote Python independente com indicadores, otimização de parâmetros, relatórios Portfolio e exportação de dados para gráficos.

**Python 3.12–3.14** · **Versão 0.2.0** · Distribuição e importação: `openbacktesting`

[Início rápido](#quick-start) · [Manual](../core/index.md) · [Exemplos](../../examples/README.md) · [Relatar um problema](https://github.com/lucidcog/openbacktesting/issues)

## Patrocinador principal — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) é o principal patrocinador pago do OpenBacktesting.** Seu apoio financeiro ajuda a custear este projeto.

O Pineify oferece programação de Pine Script assistida por IA e um editor visual para criar indicadores e estratégias do TradingView. [Conheça o Pineify →](https://pineify.app)

## O que você pode fazer

- **Criar estratégias:** use um ciclo de execução candle a candle, entradas tipadas, indicadores integrados e funções auxiliares combináveis.
- **Examinar a execução:** consulte ordens, execuções, dimensionamento de posições, taxas, operações encerradas e lotes abertos.
- **Analisar resultados:** acesse estatísticas em pandas, curvas de patrimônio e relatórios Portfolio imutáveis para cada execução.
- **Comparar parâmetros:** faça buscas em grade ou otimização opcional com SAMBO, salve experimentos e exporte dados para seu próprio renderizador de gráficos.

<a name="quick-start"></a>

## Início rápido

Instale o [uv](https://docs.astral.sh/uv/getting-started/installation/) e use Python `>=3.12,<3.15`. No terminal:

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

O exemplo usa dados históricos de GOOG incluídos no pacote; não é necessário baixar dados de mercado. Ele mostra retorno, número de operações, drawdown máximo e tabelas de resultados. Veja [seu primeiro backtest](../core/quickstart.md) para acompanhar o passo a passo.

Como alternativa, instale o código-fonte obtido em um ambiente Python existente:

```sh
python -m pip install .
```

As dependências básicas são NumPy, pandas e `pandas-ta-classic==0.8.32`. Para otimização com SAMBO, use `python -m pip install '.[optimize]'` ou `uv sync --locked --extra optimize`. Estas instruções instalam a partir do código-fonte; não pressupõem uma publicação no PyPI. [Detalhes de build e distribuição](../core/development.md).

## Backtest mínimo

Salve o código abaixo como `quickstart.py` na raiz do repositório e execute `uv run --locked python quickstart.py`:

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

Esta estratégia solicita uma unidade no primeiro candle. Por padrão, a ordem é executada na abertura do candle seguinte; `close_at_last_close` encerra a posição restante no último fechamento.

`run()` retorna uma Series do pandas. Use `result["_trades"]` para as operações e `result["_equity_curve"]` para o histórico do patrimônio. O [guia de resultados](../core/guides/results.md) contém todos os campos e a exportação de Portfolio; campos iniciados por sublinhado são diagnósticos nativos, não um contrato estável entre linguagens.

## Documentação

O manual detalhado e os exemplos estão atualmente em inglês.

| Assunto | Referência |
| --- | --- |
| Primeiros passos | [Primeiro backtest](../core/quickstart.md) · [Índice de exemplos](../../examples/README.md) |
| Estratégias e dados | [Ciclo da estratégia](../core/guides/author.md) · [Dados de mercado](../core/guides/data.md) · [API principal](../core/reference/core.md) |
| Indicadores | [Catálogo de indicadores](../core/reference/indicators/index.md) |
| Execução e otimização | [Executar estratégias](../core/guides/runtime.md) · [Experimentos de parâmetros](../core/guides/optimizer.md) |
| Resultados e gráficos | [Resultados e Portfolio](../core/guides/results.md) · [Exportar dados para gráficos](../core/guides/plotting.md) |
| Desenvolvimento | [Verificação e builds](../core/development.md) · [Limitações atuais](../core/limitations.md) |

## Escopo e compatibilidade

- O modelo opera com **um único ativo e uma única moeda de liquidação**. Os relatórios Portfolio descrevem uma execução; não são contas de carteira com múltiplos ativos.
- O pacote fornece cálculos e dados para gráficos. **Não inclui renderizador de gráficos, motor de negociação ao vivo, ambiente isolado de execução nem conversor de Pine Script**, e não promete equivalência semântica com Pine. Execute apenas código de estratégia confiável.
- O suporte ao Windows e as comparações completas com Pine não foram validados. Consulte as [limitações atuais](../core/limitations.md) sobre execução e modelagem de mercado.

A distribuição e a importação se chamam `openbacktesting`; não há pontos de entrada com nomes antigos. Arquivos pickle com caminhos de módulos antigos não são migrados automaticamente, a leitura de arquivos com identificadores de marca anteriores não é garantida e experimentos com uma identidade de execução antiga precisam ser refeitos. [Migração e procedência](../core/development.md#provenance-and-behavioral-boundaries).

## Suporte e contribuições

Use [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) para bugs, dúvidas e sugestões de funcionalidades. Inclua as versões do Python e do pacote, um exemplo mínimo que reproduza o problema e o comportamento esperado e observado. Contribuições por [pull requests](https://github.com/lucidcog/openbacktesting/pulls) são bem-vindas.

Antes de propor uma alteração de código, execute:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consulte o [guia de desenvolvimento](../core/development.md) para a lista completa de verificações. Mudanças no comportamento público exigem documentação, exemplos executáveis e validação da execução. Código, comentários e documentação técnica usam inglês por padrão; as traduções do README são conteúdo localizado intencionalmente.

## Traduções

O [README em inglês](../../README.md) é a referência principal. Há traduções para espanhol, português do Brasil, francês, alemão, italiano e hindi. Use os links de idioma acima e siga o [guia de tradução](TRANSLATING.md) ao atualizá-las. Mantenha comandos, identificadores de API, limites funcionais e reconhecimento do patrocinador consistentes.

## Licença e procedência

A licença declarada do projeto é [Apache-2.0](../../LICENSE). Materiais de terceiros mantêm suas licenças originais, incluindo os [dados de referência de indicadores](../../tests/fixtures/indicator_expansion/README.md).

O [manifesto de fontes](../../source-manifest.json) registra adaptações de uma [versão do projeto de origem sob AGPL-3.0](https://github.com/kernc/backtesting.py/blob/ca2e2611621e472542ba90f7243a1fa06a7d7108/LICENSE.md). A declaração Apache-2.0 não substitui esses termos; distribuir o código derivado somente sob Apache-2.0 exige autorização separada. O [manifesto de extração](../../extraction-manifest.json) registra a versão fonte direta e o mapeamento de caminhos.
