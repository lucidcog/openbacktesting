# OpenBacktesting

**Le backtesting historique en Python, des règles de stratégie aux résultats que vous pouvez examiner.**

[English](../../README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Português (Brasil)](README.pt-BR.md) · **Français** · [Deutsch](README.de.md) · [Italiano](README.it.md) · [हिन्दी](README.hi.md)

Écrivez des stratégies exécutées bougie par bougie, évaluez-les sur des données historiques de marché et examinez les ordres, les transactions, les capitaux propres et les statistiques de risque. OpenBacktesting est un paquet Python autonome avec indicateurs, optimisation des paramètres, rapports Portfolio et export de données pour les graphiques.

**Python 3.12–3.14** · **Version 0.2.1** · Distribution et import : `openbacktesting`

[Démarrage rapide](#quick-start) · [Manuel](https://docs.openbacktesting.com/) · [Exemples](https://docs.openbacktesting.com/examples/) · [Signaler un problème](https://github.com/lucidcog/openbacktesting/issues)

[![OpenBacktesting Studio](../core/_static/studio/backtest-results.png)](../core/_static/studio/backtest-results.png)

## Sponsor principal — Pineify

<a href="https://pineify.app">
  <img src="../assets/pineify-logo.svg" alt="Pineify" width="96">
</a>

**[Pineify](https://pineify.app) est le principal sponsor payant d'OpenBacktesting.** Son soutien financier contribue au financement du projet.

Pineify est une suite d'outils de trading basés sur l'IA pour créer des indicateurs et des stratégies sur plusieurs plateformes. Elle réunit Pine Script AI, un agent financier, la sélection d'actions par IA, le filtrage des marchés, l'analyse de graphiques et des outils MCP. [Découvrir Pineify →](https://pineify.app)

## Fonctionnalités

- **Créer des stratégies :** utilisez un cycle d'exécution bougie par bougie, des paramètres typés, des indicateurs intégrés et des fonctions auxiliaires composables.
- **Examiner l'exécution :** consultez les ordres, leurs exécutions, le dimensionnement des positions, les frais, les transactions clôturées et les lots ouverts.
- **Analyser les résultats :** accédez aux statistiques pandas, aux courbes de capitaux propres et aux rapports Portfolio immuables de chaque exécution.
- **Comparer les paramètres :** effectuez des recherches sur grille ou une optimisation optionnelle avec SAMBO, enregistrez les expériences et exportez les données pour votre propre moteur de rendu.

<a name="quick-start"></a>

## Démarrage rapide

Installez [uv](https://docs.astral.sh/uv/getting-started/installation/) et utilisez Python `>=3.12,<3.15`. Dans un terminal :

```sh
git clone https://github.com/lucidcog/openbacktesting.git
cd openbacktesting
uv sync --locked
uv run --locked python examples/advanced/run_author.py
```

L'exemple utilise les données historiques GOOG fournies avec le paquet ; aucun téléchargement de données de marché n'est nécessaire. Il affiche le rendement, le nombre de transactions, le drawdown maximal et les tableaux de résultats. Consultez [votre premier backtest](https://docs.openbacktesting.com/quickstart/) pour suivre les étapes.

Vous pouvez aussi installer les sources récupérées dans un environnement Python existant :

```sh
python -m pip install .
```

Les dépendances de base sont NumPy, pandas et `pandas-ta-classic==0.8.32`. Pour l'optimisation SAMBO, utilisez `python -m pip install '.[optimize]'` ou `uv sync --locked --extra optimize`. Ces instructions installent le paquet depuis les sources ; elles ne supposent pas une publication sur PyPI. [Détails de construction et de distribution](https://docs.openbacktesting.com/development/).

## Backtest minimal

Enregistrez ce code dans `quickstart.py` à la racine du dépôt, puis lancez `uv run --locked python quickstart.py` :

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

Cette stratégie demande l'achat d'une unité à la première bougie. Par défaut, l'ordre est exécuté à l'ouverture de la bougie suivante ; `close_at_last_close` clôture la position restante au dernier cours de clôture.

`run()` renvoie une Series pandas. Utilisez `result["_trades"]` pour les transactions et `result["_equity_curve"]` pour l'historique des capitaux propres. Le [guide des résultats](https://docs.openbacktesting.com/guides/results/) présente tous les champs et l'export Portfolio ; les champs préfixés par un trait de soulignement sont des diagnostics natifs, pas un contrat stable entre langages.

## Documentation

[Manuel](https://docs.openbacktesting.com/)

Le manuel détaillé et les exemples sont actuellement en anglais.

| Sujet | Référence |
| --- | --- |
| Premiers pas | [Premier backtest](https://docs.openbacktesting.com/quickstart/) · [Index des exemples](https://docs.openbacktesting.com/examples/) |
| Stratégies et données | [Cycle de la stratégie](https://docs.openbacktesting.com/guides/author/) · [Données de marché](https://docs.openbacktesting.com/guides/data/) · [API principale](https://docs.openbacktesting.com/reference/core/) |
| Indicateurs | [Catalogue des indicateurs](https://docs.openbacktesting.com/reference/indicators/) |
| Exécution et optimisation | [Exécuter des stratégies](https://docs.openbacktesting.com/guides/runtime/) · [Expériences de paramètres](https://docs.openbacktesting.com/guides/optimizer/) |
| Résultats et graphiques | [Résultats et Portfolio](https://docs.openbacktesting.com/guides/results/) · [Export des données graphiques](https://docs.openbacktesting.com/guides/plotting/) |
| Développement | [Vérification et construction](https://docs.openbacktesting.com/development/) · [Limites actuelles](https://docs.openbacktesting.com/limitations/) |

## Périmètre et compatibilité

- Le modèle de trading gère **un seul actif et une seule devise de règlement**. Les rapports Portfolio décrivent une exécution ; ce ne sont pas des comptes de portefeuille multi-actifs.
- Le paquet fournit des calculs et des données pour les graphiques. Il **n'inclut ni moteur de rendu graphique, ni moteur de trading en direct, ni bac à sable d'exécution, ni convertisseur Pine Script**, et ne garantit pas une sémantique équivalente à Pine. N'exécutez que du code de stratégie de confiance.
- La prise en charge de Windows et les comparaisons complètes avec Pine n'ont pas été validées. Consultez les [limites actuelles](https://docs.openbacktesting.com/limitations/) concernant l'exécution et le modèle de marché.

Le nom de distribution et d'import est `openbacktesting` ; aucun point d'entrée sous un ancien nom n'est fourni. Les fichiers pickle utilisant d'anciens chemins de modules ne sont pas migrés automatiquement, la lecture des archives portant d'anciens identifiants de marque n'est pas garantie et les expériences associées à une ancienne identité d'exécution doivent être relancées. [Migration et provenance](https://docs.openbacktesting.com/development/#provenance-and-behavioral-boundaries).

## Assistance et contributions

Utilisez [GitHub Issues](https://github.com/lucidcog/openbacktesting/issues) pour les bugs, questions et demandes de fonctionnalités. Indiquez les versions de Python et du paquet, un exemple minimal reproduisant le problème et les comportements attendu et observé. Les contributions par [pull request](https://github.com/lucidcog/openbacktesting/pulls) sont les bienvenues.

Avant de proposer une modification du code, lancez :

```sh
uv sync --locked --extra test
uv run --locked python -m pytest
uv run --locked python -m openbacktesting.test
uv run --locked python scripts/check_package.py
```

Consultez le [guide de développement](https://docs.openbacktesting.com/development/) pour l'ensemble des vérifications. Toute modification du comportement public nécessite une documentation, des exemples exécutables et une validation de leur exécution. Le code, les commentaires et la documentation technique sont en anglais par défaut ; les traductions du README sont du contenu volontairement localisé.

## Traductions

Le [README anglais](../../README.md) fait référence. Des traductions sont disponibles en chinois simplifié, espagnol, portugais du Brésil, français, allemand, italien et hindi. Utilisez les liens de langue ci-dessus et suivez le [guide de traduction](TRANSLATING.md) pour les mises à jour. Préservez la cohérence des commandes, des identifiants d'API, des limites fonctionnelles et de la mention du sponsor.

## Licence et provenance

La licence déclarée du projet est [Apache-2.0](../../LICENSE). Les éléments tiers conservent leurs licences d'origine, notamment les [données de référence des indicateurs](../../tests/fixtures/indicator_expansion/README.md).
