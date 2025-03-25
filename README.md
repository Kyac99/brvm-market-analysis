# Analyse des performances de la BRVM

Ce projet permet de collecter et d'analyser les données historiques des valeurs mobilières cotées à la Bourse Régionale des Valeurs Mobilières (BRVM) et des indices associés.

## Objectifs

- Scraper les données historiques des cours depuis les sites de la BRVM et de Sika Finance
- Analyser les performances de chaque valeur depuis le début de sa cotation
- Visualiser l'évolution des indices et des valeurs individuelles
- Comparer les performances par secteur
- Identifier les corrélations entre les différentes valeurs

## Structure du projet

```
brvm-market-analysis/
├── data/                 # Dossier contenant les données collectées (créé automatiquement)
├── notebooks/
│   └── analyse_performances.ipynb  # Notebook d'analyse des performances
├── scraper/
│   └── brvm_scraper.py   # Script de scraping des données
└── README.md             # Ce fichier
```

## Prérequis

- Python 3.6 ou plus récent
- Bibliothèques requises :
  - requests
  - beautifulsoup4
  - pandas
  - numpy
  - matplotlib
  - seaborn
  - jupyter

Vous pouvez installer toutes les dépendances nécessaires avec la commande suivante :

```bash
pip install -r requirements.txt
```

## Utilisation

### 1. Collecte des données

Pour scraper les données historiques des valeurs de la BRVM :

```bash
cd scraper
python brvm_scraper.py
```

Ce script va :
- Récupérer la liste des valeurs cotées à la BRVM
- Collecter les données historiques pour chaque valeur et pour les indices
- Sauvegarder les données au format CSV dans le dossier `data/`

### 2. Analyse des performances

Une fois les données collectées, vous pouvez ouvrir le notebook Jupyter pour l'analyse :

```bash
cd notebooks
jupyter notebook analyse_performances.ipynb
```

Le notebook permet de :
- Visualiser l'évolution des prix de chaque valeur
- Calculer les performances (rendement total, rendement annualisé, volatilité, etc.)
- Comparer les valeurs entre elles et par secteur
- Analyser les corrélations entre les différentes valeurs

## Indicateurs de performance calculés

- **Rendement total** : Performance totale depuis le début de la cotation
- **Rendement annualisé** : Performance annuelle moyenne
- **Volatilité** : Écart-type des rendements (mesure du risque)
- **Ratio de Sharpe** : Ratio rendement/risque (performance ajustée au risque)
- **Drawdown maximum** : Perte maximale subie depuis un pic

## Sources de données

- [Site officiel de la BRVM](https://www.brvm.org/)
- [Sika Finance](https://www.sikafinance.com/)

## Limitations

- Le scraping dépend de la structure des sites web, qui peut changer
- Certaines valeurs peuvent avoir des données manquantes ou incomplètes
- Les ajustements pour dividendes et opérations sur titres peuvent ne pas être pris en compte

## Contributeurs

- [Kyac99](https://github.com/Kyac99)

## Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.
