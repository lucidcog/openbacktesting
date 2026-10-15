# OpenBacktesting

**Backtesting histórico em Python, das regras da estratégia a resultados que você pode examinar.**

[English](../../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · **Português (Brasil)** · [Français](README.fr.md) · [Deutsch](README.de.md) · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Escreva estratégias executadas candle a candle, avalie-as com dados históricos de mercado e examine ordens, operações, patrimônio e estatísticas de risco. O OpenBacktesting é um pacote Python independente com indicadores, otimização de parâmetros, relatórios Portfolio e exportação de dados para gráficos.

**Python 3.12–3.14** · **Versão 0.2.1** · Distribuição e importação: `openbacktesting`

[Início rápido](#quick-start) · [Manual](https://docs.openbacktesting.com/) · [Exemplos](https://docs.openbacktesting.com/examples/) · [Relatar um problema](https://github.com/lucidcog/openbacktesting/issues)

[![OpenBacktesting Studio](../core/_static/studio/backtest-results-light.jpg)](../core/_static/studio/backtest-results-light.jpg)

## Patrocinador principal — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) é o principal patrocinador pago do OpenBacktesting.** Seu apoio financeiro ajuda a custear este projeto.

O Pineify é um conjunto de ferramentas de trading com IA para criar indicadores e estratégias em várias plataformas. Ele reúne Pine Script AI, um agente financeiro, seleção de ações com IA, filtros de mercado, análise de gráficos e ferramentas MCP. [Conheça o Pineify →](https://pineify.app)

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

O exemplo usa dados históricos de GOOG incluídos no pacote; não é necessário baixar dados de mercado. Ele mostra retorno, número de operações, drawdown máximo e tabelas de resultados. Veja [seu primeiro backtest](https://docs.openbacktesting.com/quickstart/) para acompanhar o passo a passo.

Como alternativa, instale o código-fonte obtido em um ambiente Python existente:

```sh
python -m pip install .
```

As dependências básicas são NumPy, pandas e `pandas-ta-classic==0.8.32`. Para otimização com SAMBO, use `python -m pip install '.[optimize]'` ou `uv sync --locked --extra optimize`. Estas instruções instalam a partir do código-fonte; não pressupõem uma publicação no PyPI. [Detalhes de build e distribuição](https://docs.openbacktesting.com/development/).

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

`run()` retorna uma Series do pandas. Use `result["_trades"]` para as operações e `result["_equity_curve"]` para o histórico do patrimônio. O [guia de resultados](https://docs.openbacktesting.com/guides/results/) contém todos os campos e a exportação de Portfolio; campos iniciados por sublinhado são diagnósticos nativos, não um contrato estável entre linguagens.

## Documentação

[Manual](https://docs.openbacktesting.com/)

O manual detalhado e os exemplos estão atualmente em inglês.

| Assunto | Referência |
| --- | --- |
| Primeiros passos | [Primeiro backtest](https://docs.openbacktesting.com/quickstart/) · [Índice de exemplos](https://docs.openbacktesting.com/examples/) |
| Estratégias e dados | [Ciclo da estratégia](https://docs.openbacktesting.com/guides/author/) · [Dados de mercado](https://docs.openbacktesting.com/guides/data/) · [API principal](https://docs.openbacktesting.com/reference/core/) |
| Indicadores | [Catálogo de indicadores](https://docs.openbacktesting.com/reference/indicators/) |
| Execução e otimização | [Executar estratégias](https://docs.openbacktesting.com/guides/runtime/) · [Experimentos de parâmetros](https://docs.openbacktesting.com/guides/optimizer/) |
| Resultados e gráficos | [Resultados e Portfolio](https://docs.openbacktesting.com/guides/results/) · [Exportar dados para gráficos](https://docs.openbacktesting.com/guides/plotting/) |
| Desenvolvimento | [Verificação e builds](https://docs.openbacktesting.com/development/) · [Limitações atuais](https://docs.openbacktesting.com/limitations/) |

## Escopo e compatibilidade

- O modelo opera com **um único ativo e uma única moeda de liquidação**. Os relatórios Portfolio descrevem uma execução; não são contas de carteira com múltiplos ativos.
- O pacote fornece cálculos e dados para gráficos. **Não inclui renderizador de gráficos, motor de negociação ao vivo, ambiente isolado de execução nem conversor de Pine Script**, e não promete equivalência semântica com Pine. Execute apenas código de estratégia confiável.
- O suporte ao Windows e as comparações completas com Pine não foram validados. Consulte as [limitações atuais](https://docs.openbacktesting.com/limitations/) sobre execução e modelagem de mercado.

A distribuição e a importação se chamam `openbacktesting`; não há pontos de entrada com nomes antigos. Arquivos pickle com caminhos de módulos antigos não são migrados automaticamente, a leitura de arquivos com identificadores de marca anteriores não é garantida e experimentos com uma identidade de execução antiga precisam ser refeitos. [Migração e procedência](https://docs.openbacktesting.com/development/#provenance-and-behavioral-boundaries).

## Suporte e contribuições

Use [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) para bugs, dúvidas e sugestões de funcionalidades. Inclua as versões do Python e do pacote, um exemplo mínimo que reproduza o problema e o comportamento esperado e observado. Contribuições por [pull requests](https://github.com/lucidcog/openbacktesting/pulls) são bem-vindas.

Antes de propor uma alteração de código, execute:

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consulte o [guia de desenvolvimento](https://docs.openbacktesting.com/development/) para a lista completa de verificações. Mudanças no comportamento público exigem documentação, exemplos executáveis e validação da execução. Código, comentários e documentação técnica usam inglês por padrão; as traduções do README são conteúdo localizado intencionalmente.

## Traduções

O [README em inglês](../../README.md) é a referência principal. Há traduções para chinês simplificado, espanhol, português do Brasil, francês, alemão, italiano e hindi. Use os links de idioma acima e siga o [guia de tradução](TRANSLATING.md) ao atualizá-las. Mantenha comandos, identificadores de API, limites funcionais e reconhecimento do patrocinador consistentes.

## Licença e procedência

A licença declarada do projeto é [Apache-2.0](../../LICENSE). Materiais de terceiros mantêm suas licenças originais, incluindo os [dados de referência de indicadores](../../tests/fixtures/indicator_expansion/README.md).
